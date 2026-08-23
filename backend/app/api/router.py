from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.doctors import router as doctors_router
from app.api.admin import router as admin_router
from app.api.appointments import router as appointments_router
from app.api.doctor import router as doctor_portal_router
from app.api.calendar import router as calendar_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(doctors_router)
api_router.include_router(admin_router)
api_router.include_router(appointments_router)
api_router.include_router(doctor_portal_router)
api_router.include_router(calendar_router)
