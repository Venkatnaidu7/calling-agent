from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from apps.api.models.call_log import CallLog
from apps.api.schemas.call_log import CallLogFilter, CallLogResponse, CallTranscriptResponse, CallStatsResponse
from apps.api.schemas.common import PaginationParams, PaginatedResponse
from apps.api.repositories.call_log_repo import CallLogRepository


class CallLogService:
    def __init__(self, session: AsyncSession, tenant_id: Optional[UUID] = None):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = CallLogRepository(session, tenant_id=tenant_id)

    async def create_log(self, data: dict) -> CallLog:
        log = await self.repo.create(**data)
        await self.session.commit()
        return log

    async def update_log(self, call_id: str, **updates) -> Optional[CallLog]:
        log = await self.repo.get_by_call_id(call_id)
        if not log:
            return None
        updated = await self.repo.update(log.id, **updates)
        await self.session.commit()
        return updated

    async def get_log(self, call_id: str) -> CallLogResponse:
        log = await self.repo.get_by_call_id(call_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call record not found")
        return CallLogResponse.model_validate(log)

    async def list_logs(
        self,
        filters: CallLogFilter,
        pagination: PaginationParams,
    ) -> PaginatedResponse[CallLogResponse]:
        items, total = await self.repo.list_by_filter(filters, pagination)
        pages = (total + pagination.per_page - 1) // pagination.per_page if total > 0 else 0
        return PaginatedResponse(
            items=[CallLogResponse.model_validate(i) for i in items],
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            pages=pages,
        )

    async def get_transcript(self, call_id: str) -> CallTranscriptResponse:
        log = await self.repo.get_by_call_id(call_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Call record not found")
        return CallTranscriptResponse(
            call_id=log.call_id,
            transcript=log.transcript,
            summary=log.summary,
            sentiment=log.sentiment,
        )

    async def get_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> CallStatsResponse:
        stats = await self.repo.get_stats(date_from, date_to)
        return CallStatsResponse(**stats)

    async def save_transcript(self, call_id: str, transcript: list) -> None:
        await self.update_log(call_id, transcript=transcript)

    async def save_recording(self, call_id: str, recording_url: str, duration: int) -> None:
        await self.update_log(call_id, recording_url=recording_url, recording_duration=duration)
