"""
Create Initial Platform Administrator Account

Usage:
    python scripts/create_platform_admin.py --email admin@example.com --password "YourSecurePassword"
"""

import asyncio
import argparse
from apps.api.database import async_session_factory
from apps.api.models.tenant import Tenant
from apps.api.models.user import User
from apps.api.utils.crypto import hash_password
from sqlalchemy import select


async def create_platform_admin(
    email: str, password: str, first_name: str = "Super", last_name: str = "Admin"
):
    async with async_session_factory() as session:
        # 1. Check if user already exists
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()
        if existing_user:
            print(f"[-] Error: User with email '{email}' already exists.")
            return

        # 2. Check or create system root tenant
        stmt = select(Tenant).where(Tenant.slug == "platform-admin-root")
        result = await session.execute(stmt)
        system_tenant = result.scalars().first()

        if not system_tenant:
            system_tenant = Tenant(
                name="Platform Administration",
                slug="platform-admin-root",
                business_name="Aicalling Master Platform",
                timezone="UTC",
                status="active",
                settings={"type": "root_system"},
            )
            session.add(system_tenant)
            await session.flush()
            print("[+] Created Master Platform Admin Tenant.")

        # 3. Create the PLATFORM_ADMIN user
        admin_user = User(
            tenant_id=system_tenant.id,
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role="PLATFORM_ADMIN",
            is_active=True,
            email_verified=True,
        )
        session.add(admin_user)
        await session.commit()

        print("\n[SUCCESS] Platform Super Admin account created successfully!")
        print(f"  Email: {email}")
        print("  Role:  PLATFORM_ADMIN")
        print("  You can now log in at /login with these credentials.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Create the master Platform Administrator account."
    )
    parser.add_argument("--email", required=True, help="Master Admin Email address")
    parser.add_argument("--password", required=True, help="Master Admin Password")
    parser.add_argument("--first-name", default="Super", help="First name")
    parser.add_argument("--last-name", default="Admin", help="Last name")

    args = parser.parse_args()
    asyncio.run(create_platform_admin(args.email, args.password, args.first_name, args.last_name))


if __name__ == "__main__":
    main()
