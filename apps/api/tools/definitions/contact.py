import uuid
from typing import Any
import structlog
from apps.api.tools.registry import ToolRegistry, ToolDefinition
from apps.api.database import async_session_factory
from apps.api.repositories.contact_repo import ContactRepository

logger = structlog.get_logger()


async def get_customer(phone_number: str, _context: dict = None, **kwargs) -> dict[str, Any]:
    """Look up customer info by phone number in the tenant's database."""
    tenant_id_str = _context.get("tenant_id") if _context else None
    logger.info("get_customer_requested", phone_number=phone_number, tenant_id=tenant_id_str)

    if not tenant_id_str:
        return {"found": False, "message": "No tenant context available"}

    # SECURITY: Prevent PII leakage by only allowing lookups for the active caller's phone number
    allowed_numbers = [
        _context.get("from_number") if _context else None,
        _context.get("to_number") if _context else None,
    ]
    if phone_number not in allowed_numbers:
        logger.warning("unauthorized_customer_lookup_prevented", requested=phone_number)
        return {"found": False, "message": "Unauthorized: Can only retrieve info for the active caller."}

    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        async with async_session_factory() as session:
            repo = ContactRepository(session, tenant_id=tenant_uuid)
            contact = await repo.get_by_phone(phone_number)
            if contact:
                return {
                    "found": True,
                    "customer": {
                        "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip()
                        or "Customer",
                        "phone_number": contact.phone_number,
                        "email": contact.email,
                        "company": contact.company,
                        "customer_id": str(contact.id),
                        "notes": contact.notes,
                        "do_not_call": contact.do_not_call,
                    },
                }
    except Exception as e:
        logger.error("get_customer_error", error=str(e))

    return {"found": False, "message": f"No customer found for number {phone_number}"}


async def create_lead(
    name: str = None,
    phone_number: str = None,
    email: str = None,
    notes: str = None,
    _context: dict = None,
    **kwargs,
) -> dict[str, Any]:
    """Create a new lead/contact in the tenant's CRM."""
    tenant_id_str = _context.get("tenant_id") if _context else None
    logger.info(
        "create_lead_requested", name=name, phone_number=phone_number, tenant_id=tenant_id_str
    )

    if not tenant_id_str:
        return {"created": False, "message": "Missing tenant context"}

    # SECURITY: Enforce caller identity
    allowed_numbers = [
        _context.get("from_number") if _context else None,
        _context.get("to_number") if _context else None,
    ]
    if phone_number and phone_number not in allowed_numbers:
        return {"created": False, "message": "Unauthorized: Can only create lead for active caller."}

    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        first_name = name.split()[0] if name else "Lead"
        last_name = " ".join(name.split()[1:]) if name and len(name.split()) > 1 else ""

        async with async_session_factory() as session:
            repo = ContactRepository(session, tenant_id=tenant_uuid)
            existing = await repo.get_by_phone(phone_number)
            if existing:
                return {
                    "created": True,
                    "lead_id": str(existing.id),
                    "message": f"Contact with number {phone_number} already existed; record referenced.",
                }

            contact = await repo.create(
                tenant_id=tenant_uuid,
                phone_number=phone_number or "+10000000000",
                first_name=first_name,
                last_name=last_name,
                email=email,
                notes=notes,
                status="active",
            )
            await session.commit()
            return {
                "created": True,
                "lead_id": str(contact.id),
                "message": f"Lead created successfully for {name or 'Customer'}",
            }
    except Exception as e:
        logger.error("create_lead_error", error=str(e))
        return {"created": False, "error": str(e)}


async def update_customer(
    customer_id: str, updates: dict, _context: dict = None, **kwargs
) -> dict[str, Any]:
    """Update customer information in tenant CRM."""
    tenant_id_str = _context.get("tenant_id") if _context else None
    logger.info(
        "update_customer_requested",
        customer_id=customer_id,
        updates=updates,
        tenant_id=tenant_id_str,
    )

    if not tenant_id_str:
        return {"updated": False, "message": "Missing tenant context"}

    try:
        tenant_uuid = uuid.UUID(tenant_id_str)
        c_uuid = uuid.UUID(customer_id)
        
        async with async_session_factory() as session:
            repo = ContactRepository(session, tenant_id=tenant_uuid)
            existing = await repo.get_by_id(c_uuid)
            
            # SECURITY: Enforce caller identity to prevent IDOR
            allowed_numbers = [
                _context.get("from_number") if _context else None,
                _context.get("to_number") if _context else None,
            ]
            if not existing or existing.phone_number not in allowed_numbers:
                return {"updated": False, "message": "Unauthorized: Can only update active caller's record."}
                
            await repo.update(c_uuid, **updates)
            await session.commit()
            return {
                "updated": True,
                "customer_id": customer_id,
                "message": "Customer record updated successfully",
            }
    except Exception as e:
        logger.error("update_customer_error", error=str(e))
        return {"updated": False, "error": str(e)}


def register_contact_tools():
    ToolRegistry.register(
        ToolDefinition(
            name="get_customer",
            description="Look up customer info by phone number",
            parameters={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Customer phone number to look up",
                    },
                },
                "required": ["phone_number"],
            },
            handler=get_customer,
            category="contact",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="create_lead",
            description="Create a new lead or contact",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Lead name"},
                    "phone_number": {"type": "string", "description": "Lead phone number"},
                    "email": {"type": "string", "description": "Lead email address"},
                    "notes": {"type": "string", "description": "Additional notes for the lead"},
                },
            },
            handler=create_lead,
            category="contact",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="update_customer",
            description="Update customer information",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID to update"},
                    "updates": {
                        "type": "object",
                        "description": "Key-value pairs of fields to update",
                    },
                },
                "required": ["customer_id", "updates"],
            },
            handler=update_customer,
            category="contact",
        )
    )
