from typing import Any
import structlog
from apps.api.tools.registry import ToolRegistry, ToolDefinition

logger = structlog.get_logger()


async def check_availability(
    date: str = None, service: str = None, provider: str = None, _context: dict = None, **kwargs
) -> dict[str, Any]:
    """Check appointment availability. In production, this calls the calendar provider."""
    tenant_id = _context["tenant_id"] if _context else None
    logger.info("checking_availability", date=date, service=service, tenant_id=tenant_id)

    # TODO: Integrate with CalendarProvider
    # For now, return a structured response that the AI can use
    return {
        "available": True,
        "slots": [
            {"date": date or "2026-09-10", "time": "10:00 AM", "duration_minutes": 30},
            {"date": date or "2026-09-10", "time": "2:00 PM", "duration_minutes": 30},
            {"date": date or "2026-09-11", "time": "11:00 AM", "duration_minutes": 30},
        ],
        "message": "Found available slots",
    }


async def book_appointment(
    date: str,
    time: str,
    customer_name: str = None,
    customer_phone: str = None,
    service: str = None,
    notes: str = None,
    _context: dict = None,
    **kwargs,
) -> dict[str, Any]:
    """Book an appointment and persist it into the database."""
    import uuid
    from datetime import datetime, timezone
    from apps.api.database import async_session_factory
    from apps.api.repositories.contact_repo import ContactRepository

    tenant_id_str = _context.get("tenant_id") if _context else None
    # SECURITY FIX: Verify customer_phone matches the actual caller's phone number
    actual_caller_phone = _context.get("from_number") if _context else None

    if customer_phone and actual_caller_phone and customer_phone != actual_caller_phone:
        logger.warning(
            "tool_phone_mismatch", customer_phone=customer_phone, actual=actual_caller_phone
        )
        return {
            "booked": False,
            "error": "You can only book appointments for your own phone number.",
            "message": "Security verification failed: phone number mismatch.",
        }

    logger.info(
        "booking_appointment", date=date, time=time, tenant_id=tenant_id_str, customer=customer_name
    )

    appointment_id = str(uuid.uuid4())
    appt_record = {
        "id": appointment_id,
        "date": date,
        "time": time,
        "service": service or "General Consultation",
        "notes": notes or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed",
    }

    if tenant_id_str and customer_phone:
        try:
            tenant_uuid = uuid.UUID(tenant_id_str)
            async with async_session_factory() as session:
                repo = ContactRepository(session, tenant_id=tenant_uuid)
                contact = await repo.get_by_phone(customer_phone)
                if not contact:
                    first_name = customer_name.split()[0] if customer_name else "Customer"
                    last_name = (
                        " ".join(customer_name.split()[1:])
                        if customer_name and len(customer_name.split()) > 1
                        else ""
                    )
                    contact = await repo.create(
                        tenant_id=tenant_uuid,
                        phone_number=customer_phone,
                        first_name=first_name,
                        last_name=last_name,
                        custom_fields={"appointments": [appt_record]},
                    )
                else:
                    c_fields = dict(contact.custom_fields or {})
                    existing_appts = c_fields.get("appointments", [])
                    existing_appts.append(appt_record)
                    c_fields["appointments"] = existing_appts
                    await repo.update(contact.id, custom_fields=c_fields)
                await session.commit()
                logger.info("appointment_persisted_to_db", appointment_id=appointment_id)
        except Exception as e:
            logger.error("appointment_persistence_error", error=str(e))

    return {
        "booked": True,
        "appointment_id": appointment_id,
        "date": date,
        "time": time,
        "service": service or "General Consultation",
        "message": f"Appointment successfully confirmed for {date} at {time}.",
    }


async def cancel_appointment(
    appointment_id: str, reason: str = None, _context: dict = None, **kwargs
) -> dict[str, Any]:
    """Cancel an existing appointment in the database."""
    logger.info("cancelling_appointment", appointment_id=appointment_id, reason=reason)

    tenant_id_str = _context.get("tenant_id") if _context else None
    actual_caller_phone = _context.get("from_number") if _context else None

    if tenant_id_str and actual_caller_phone:
        try:
            import uuid
            from apps.api.database import async_session_factory
            from apps.api.repositories.contact_repo import ContactRepository

            tenant_uuid = uuid.UUID(tenant_id_str)
            async with async_session_factory() as session:
                repo = ContactRepository(session, tenant_id=tenant_uuid)
                contact = await repo.get_by_phone(actual_caller_phone)

                if contact and contact.custom_fields and "appointments" in contact.custom_fields:
                    appts = contact.custom_fields["appointments"]
                    updated = False
                    for appt in appts:
                        if appt.get("id") == appointment_id:
                            appt["status"] = "cancelled"
                            appt["cancellation_reason"] = reason
                            updated = True
                            break

                    if updated:
                        c_fields = dict(contact.custom_fields)
                        c_fields["appointments"] = appts
                        await repo.update(contact.id, custom_fields=c_fields)
                        await session.commit()
                        logger.info("appointment_cancelled_in_db", appointment_id=appointment_id)
                        return {
                            "cancelled": True,
                            "appointment_id": appointment_id,
                            "message": f"Appointment {appointment_id} has been cancelled.",
                        }
                    else:
                        return {
                            "cancelled": False,
                            "error": "Appointment not found for this caller."
                        }
        except Exception as e:
            logger.error("appointment_cancellation_error", error=str(e))
            return {"cancelled": False, "error": "Internal database error"}

    return {
        "cancelled": False,
        "error": "Could not identify caller context to cancel appointment."
    }


# Register tools
def register_appointment_tools():
    ToolRegistry.register(
        ToolDefinition(
            name="check_availability",
            description="Check available appointment slots for a given date, service, or provider",
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date to check in YYYY-MM-DD format"},
                    "service": {
                        "type": "string",
                        "description": "Service type to check availability for",
                    },
                    "provider": {"type": "string", "description": "Specific provider/staff member"},
                },
            },
            handler=check_availability,
            category="appointment",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="book_appointment",
            description="Book an appointment at a specific date and time",
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Appointment date (YYYY-MM-DD)"},
                    "time": {"type": "string", "description": "Appointment time (e.g. 10:00 AM)"},
                    "customer_name": {"type": "string", "description": "Customer's name"},
                    "customer_phone": {"type": "string", "description": "Customer's phone number"},
                    "service": {"type": "string", "description": "Service type"},
                    "notes": {"type": "string", "description": "Additional notes"},
                },
                "required": ["date", "time"],
            },
            handler=book_appointment,
            requires_confirmation=True,
            category="appointment",
        )
    )

    ToolRegistry.register(
        ToolDefinition(
            name="cancel_appointment",
            description="Cancel an existing appointment by its ID",
            parameters={
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The appointment ID to cancel",
                    },
                    "reason": {"type": "string", "description": "Reason for cancellation"},
                },
                "required": ["appointment_id"],
            },
            handler=cancel_appointment,
            requires_confirmation=True,
            category="appointment",
        )
    )
