import pytest
from datetime import date, time


@pytest.mark.asyncio
async def test_admin_doctor_crud_and_rbac(async_client):
    """Test admin doctor creation, editing, working hours, and RBAC authorization."""
    # 1. Register Admin User
    admin_reg = {
        "email": "admin@healthy.com",
        "password": "AdminPassword123!",
        "full_name": "System Admin",
        "role": "ADMIN"
    }
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin@healthy.com", "password": "AdminPassword123!"})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register Patient User
    patient_reg = {
        "email": "patient@healthy.com",
        "password": "PatientPassword123!",
        "full_name": "Test Patient",
        "role": "PATIENT"
    }
    await async_client.post("/api/auth/register", json=patient_reg)
    patient_login = await async_client.post("/api/auth/login", json={"email": "patient@healthy.com", "password": "PatientPassword123!"})
    patient_token = patient_login.json()["access_token"]
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    # 3. Patient attempting to create a doctor returns HTTP 403
    doc_create_payload = {
        "email": "dr.smith@healthy.com",
        "password": "DoctorPassword123!",
        "full_name": "Dr. Alice Smith",
        "specialisation": "Cardiology",
        "bio": "Expert cardiologist",
        "slot_duration_minutes": 30,
        "timezone": "UTC",
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
            {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00"}
        ]
    }
    forbidden_resp = await async_client.post("/api/admin/doctors", json=doc_create_payload, headers=patient_headers)
    assert forbidden_resp.status_code == 403

    # 4. Admin creating doctor succeeds
    create_resp = await async_client.post("/api/admin/doctors", json=doc_create_payload, headers=admin_headers)
    assert create_resp.status_code == 201
    doctor_data = create_resp.json()
    doctor_id = doctor_data["id"]
    assert doctor_data["specialisation"] == "Cardiology"
    assert len(doctor_data["working_hours"]) == 2

    # 5. Patient listing doctors by specialization
    search_resp = await async_client.get("/api/doctors?specialisation=Cardio")
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["id"] == doctor_id

    # 6. Admin adding leave day for doctor
    leave_payload = {"leave_date": "2026-09-01", "reason": "Medical Conference"}
    leave_resp = await async_client.post(f"/api/admin/doctors/{doctor_id}/leave", json=leave_payload, headers=admin_headers)
    assert leave_resp.status_code == 201
    leave_id = leave_resp.json()["id"]

    # 7. Duplicate leave date fails with 400 LEAVE_EXISTS
    dup_leave_resp = await async_client.post(f"/api/admin/doctors/{doctor_id}/leave", json=leave_payload, headers=admin_headers)
    assert dup_leave_resp.status_code == 400
    assert dup_leave_resp.json()["error"]["code"] == "LEAVE_EXISTS"

    # 8. Admin revoking leave
    revoke_resp = await async_client.delete(f"/api/admin/doctors/leave/{leave_id}", headers=admin_headers)
    assert revoke_resp.status_code == 204
