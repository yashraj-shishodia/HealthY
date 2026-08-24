import asyncio
import uuid
from datetime import time
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorWorkingHours
from app.core.security import get_password_hash


async def seed_database():
    """Seed demo admin, doctor (Rohit Sharma, Virat Kohli, Dr. Amrita, etc.), and patient accounts."""
    async with AsyncSessionLocal() as db:
        print("🌱 Seeding database with initial demo accounts...")

        # 1. Admin User
        admin_email = "admin@healthy.com"
        result = await db.execute(select(User).where(User.email == admin_email))
        if not result.scalars().first():
            admin = User(
                id=uuid.uuid4(),
                email=admin_email,
                password_hash=get_password_hash("Password123!"),
                full_name="System Admin",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            print("  ✅ Created Admin: admin@healthy.com / Password123!")

        # Helper to seed doctors
        doctors_to_seed = [
            {
                "email": "rohit@healthy.com",
                "full_name": "Dr. Rohit Sharma",
                "specialisation": "Cardiology & Vascular Health",
                "bio": "Senior Consultant Cardiologist specializing in preventive cardiology and heart health.",
            },
            {
                "email": "virat@healthy.com",
                "full_name": "Dr. Virat Kohli",
                "specialisation": "Neurology & Sports Performance",
                "bio": "Lead Neurologist specializing in cognitive performance and neuromuscular health.",
            },
            {
                "email": "doctor@healthy.com",
                "full_name": "Dr. Amrita",
                "specialisation": "General Medicine",
                "bio": "Primary care physician dedicated to comprehensive wellness and preventative healthcare.",
            },
            {
                "email": "ujjwal@healthy.com",
                "full_name": "Dr. Ujjwal",
                "specialisation": "Pediatrics & Family Care",
                "bio": "Pediatric specialist focused on child development and family healthcare.",
            },
        ]

        for doc_info in doctors_to_seed:
            res = await db.execute(select(User).where(User.email == doc_info["email"]))
            doc_user = res.scalars().first()
            if not doc_user:
                doc_user = User(
                    id=uuid.uuid4(),
                    email=doc_info["email"],
                    password_hash=get_password_hash("Password123!"),
                    full_name=doc_info["full_name"],
                    role=UserRole.DOCTOR,
                    is_active=True,
                )
                db.add(doc_user)
                await db.flush()

                doc_profile = DoctorProfile(
                    id=uuid.uuid4(),
                    user_id=doc_user.id,
                    specialisation=doc_info["specialisation"],
                    bio=doc_info["bio"],
                    slot_duration_minutes=30,
                    timezone="UTC",
                    is_active=True,
                )
                db.add(doc_profile)
                await db.flush()

                for day in range(0, 5):
                    wh = DoctorWorkingHours(
                        id=uuid.uuid4(),
                        doctor_id=doc_profile.id,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                    )
                    db.add(wh)
                print(f"  ✅ Created Doctor: {doc_info['email']} ({doc_info['full_name']})")
            else:
                # Update existing doctor name to Dr. Amrita if doctor@healthy.com
                doc_user.full_name = doc_info["full_name"]

        # 3. Patient User
        patient_email = "patient@healthy.com"
        result = await db.execute(select(User).where(User.email == patient_email))
        patient_user = result.scalars().first()
        if not patient_user:
            patient_user = User(
                id=uuid.uuid4(),
                email=patient_email,
                password_hash=get_password_hash("Password123!"),
                full_name="Yashraj Shishodia",
                role=UserRole.PATIENT,
                is_active=True,
            )
            db.add(patient_user)
            print("  ✅ Created Patient: patient@healthy.com (Yashraj Shishodia)")
        else:
            patient_user.full_name = "Yashraj Shishodia"

        await db.commit()
        print("🌱 Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
