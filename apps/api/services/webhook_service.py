import hmac
import hashlib
import json
import secrets
import structlog
import httpx
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from apps.api.models.billing import WebhookEndpoint
from apps.api.schemas.webhook import WebhookEndpointCreate, WebhookEndpointUpdate, WebhookEndpointResponse, WebhookEndpointWithSecretResponse
from apps.api.repositories.webhook_repo import WebhookRepository

logger = structlog.get_logger()


class WebhookService:
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = WebhookRepository(session, tenant_id=tenant_id)

    async def create_endpoint(self, data: WebhookEndpointCreate) -> WebhookEndpointWithSecretResponse:
        import socket
        import ipaddress
        from urllib.parse import urlparse

        parsed = urlparse(data.url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook URL must be a valid http or https URL.")

        try:
            addr_info = socket.getaddrinfo(parsed.hostname, None)
            for entry in addr_info:
                ip = ipaddress.ip_address(entry[4][0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Webhook URL cannot target internal, private, or local network addresses.",
                    )
        except socket.gaierror:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not resolve webhook hostname.")

        secret = f"whsec_{secrets.token_hex(24)}"
        endpoint = await self.repo.create(
            tenant_id=self.tenant_id,
            url=data.url,
            secret=secret,
            description=data.description,
            events=data.events,
            is_active=True,
        )
        await self.session.commit()

        resp = WebhookEndpointWithSecretResponse(
            id=endpoint.id,
            tenant_id=endpoint.tenant_id,
            url=endpoint.url,
            secret=secret,
            description=endpoint.description,
            events=endpoint.events,
            is_active=endpoint.is_active,
            created_at=endpoint.created_at,
            updated_at=endpoint.updated_at,
        )
        return resp

    async def list_endpoints(self) -> List[WebhookEndpointResponse]:
        endpoints = await self.repo.get_active_endpoints(self.tenant_id)
        return [WebhookEndpointResponse.model_validate(e) for e in endpoints]

    async def delete_endpoint(self, endpoint_id: UUID) -> None:
        endpoint = await self.repo.get_by_id(endpoint_id)
        if not endpoint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found")
        await self.repo.delete(endpoint_id)
        await self.session.commit()

    async def dispatch_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Asynchronously dispatch an event to all subscribed endpoints."""
        endpoints = await self.repo.get_active_endpoints(self.tenant_id)
        if not endpoints:
            return

        body = json.dumps({
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        })

        async def _send_one(client: httpx.AsyncClient, ep):
            if "*" not in ep.events and event_type not in ep.events:
                return

            signature = hmac.new(
                ep.secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": event_type,
            }

            try:
                resp = await client.post(ep.url, content=body, headers=headers)
                logger.info("webhook_dispatched", url=ep.url, event=event_type, status_code=resp.status_code)
            except Exception as e:
                logger.warning("webhook_dispatch_failed", url=ep.url, event=event_type, error=str(e))

        import asyncio
        async with httpx.AsyncClient(timeout=10.0) as client:
            await asyncio.gather(*[_send_one(client, ep) for ep in endpoints], return_exceptions=True)
