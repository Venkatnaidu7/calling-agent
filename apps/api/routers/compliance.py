from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from apps.api.database import get_db
from apps.api.dependencies import get_tenant_context, require_roles
from apps.api.schemas.compliance import (
    DNCEntryCreate,
    DNCEntryResponse,
    ConsentRecordCreate,
    ConsentRecordResponse,
)
from apps.api.services.compliance_service import ComplianceService
from apps.api.models.user import User
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


def get_compliance_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[UUID, Depends(get_tenant_context)],
) -> ComplianceService:
    return ComplianceService(session, tenant_id)


class ImportDNCRequest(BaseModel):
    phone_numbers: List[str]
    source: str = "imported"


@router.get("/dnc/{phone_number}")
async def check_can_call(
    phone_number: str,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    can_call = await service.check_can_call(phone_number, service.tenant_id)
    return {"phone_number": phone_number, "can_call": can_call}


@router.post("/dnc", response_model=DNCEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_to_dnc(
    data: DNCEntryCreate,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    return await service.add_to_dnc(data.phone_number, data.source, data.reason)


@router.delete("/dnc/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_dnc(
    phone_number: str,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    success = await service.remove_from_dnc(phone_number)
    if not success:
        raise HTTPException(status_code=404, detail="DNC entry not found")


@router.post("/consent", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED)
async def record_consent(
    data: ConsentRecordCreate,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    return await service.record_consent(
        data.phone_number, data.consent_type, data.status, data.source, data.contact_id
    )


@router.post("/dnc/import")
async def import_dnc_list(
    data: ImportDNCRequest,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    count = await service.import_dnc_list(data.phone_numbers, data.source)
    return {"imported_count": count}


class CallingHoursRequest(BaseModel):
    contact_timezone: str
    calling_hours_start: str
    calling_hours_end: str


@router.post("/check-hours")
async def check_calling_hours(
    data: CallingHoursRequest,
    service: Annotated[ComplianceService, Depends(get_compliance_service)],
    user: Annotated[
        User, Depends(require_roles(["TENANT_OWNER", "TENANT_ADMIN", "COMPLIANCE_MANAGER"]))
    ],
):
    is_within = service.check_calling_hours(
        data.contact_timezone, data.calling_hours_start, data.calling_hours_end
    )
    return {"is_within_calling_hours": is_within}
