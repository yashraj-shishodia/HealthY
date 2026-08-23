import pytest
import uuid


@pytest.mark.asyncio
async def test_rbac_security_boundaries(async_client):
    """CRITICAL RBAC SECURITY AUDIT TEST:
    Verify backend RBAC authorization guards across unauthenticated, cross-role, and cross-resource access attempts.
    """
    # 1. Setup Admin, Doctor A, Doctor B, Patient A, Patient B
    admin_reg = {"email": "admin.rbac@healthy.com", "password": "AdminPassword123!", "full_name": "Admin RBAC", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.rbac@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    docA_req = {
        "email": "dr.rbacA@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. RBAC A",
        "specialisation": "Neurology",
        "slot_duration_minutes": 30,
        "working_hours": [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}]
    }
    docA_resp = await async_client.post("/api/admin/doctors", json=docA_req, headers=admin_headers)
    docA_id = docA_resp.json()["id"]

    docA_login = await async_client.post("/api/auth/login", json={"email": "dr.rbacA@healthy.com", "password": "DocPassword123!"})
    docA_headers = {"Authorization": f"Bearer {docA_login.json()['access_token']}"}

    docB_req = {
        "email": "dr.rbacB@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. RBAC B",
        "specialisation": "Pediatrics",
        "slot_duration_minutes": 30,
        "working_hours": [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}]
    }
    docB_resp = await async_client.post("/api/admin/doctors", json=docB_req, headers=admin_headers)
    docB_id = docB_resp.json()["id"]

    docB_login = await async_client.post("/api/auth/login", json={"email": "dr.rbacB@healthy.com", "password": "DocPassword123!"})
    docB_headers = {"Authorization": f"Bearer {docB_login.json()['access_token']}"}

    patientA_reg = {"email": "patientA.rbac@healthy.com", "password": "PatientPassword123!", "full_name": "Patient A RBAC", "role": "PATIENT"}
    await async_client.post("/api/auth/register", json=patientA_reg)
    patientA_login = await async_client.post("/api/auth/login", json={"email": "patientA.rbac@healthy.com", "password": "PatientPassword123!"})
    patientA_headers = {"Authorization": f"Bearer {patientA_login.json()['access_token']}"}

    patientB_reg = {"email": "patientB.rbac@healthy.com", "password": "PatientPassword123!", "full_name": "Patient B RBAC", "role": "PATIENT"}
    await async_client.post("/api/auth/register", json=patientB_reg)
    patientB_login = await async_client.post("/api/auth/login", json={"email": "patientB.rbac@healthy.com", "password": "PatientPassword123!"})
    patientB_headers = {"Authorization": f"Bearer {patientB_login.json()['access_token']}"}

    # Test 1: Unauthenticated request -> HTTP 401 Unauthorized
    unauth_resp = await async_client.get("/api/appointments/my")
    assert unauth_resp.status_code == 401

    # Test 2: Patient accessing Doctor endpoint -> HTTP 403 Forbidden
    patient_to_doc_resp = await async_client.get("/api/doctor/appointments", headers=patientA_headers)
    assert patient_to_doc_resp.status_code == 403

    # Test 3: Patient accessing Admin endpoint -> HTTP 403 Forbidden
    patient_to_admin_resp = await async_client.post("/api/admin/doctors", json=docA_req, headers=patientA_headers)
    assert patient_to_admin_resp.status_code == 403

    # Test 4: Doctor accessing Admin endpoint -> HTTP 403 Forbidden
    doc_to_admin_resp = await async_client.post("/api/admin/doctors", json=docA_req, headers=docA_headers)
    assert doc_to_admin_resp.status_code == 403

    # Patient A books an appointment with Doctor A
    booking_payload = {
        "doctor_id": docA_id,
        "appointment_date": "2026-08-24",
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "symptoms": "RBAC security check"
    }
    book_resp = await async_client.post("/api/appointments", json=booking_payload, headers=patientA_headers)
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # Test 5: Patient B attempting to view Patient A's appointment -> HTTP 403 Forbidden
    patB_view_resp = await async_client.get(f"/api/appointments/{appt_id}", headers=patientB_headers)
    assert patB_view_resp.status_code in [403, 404]

    # Test 6: Doctor B attempting to view / complete Doctor A's appointment -> HTTP 404/403
    docB_view_resp = await async_client.get(f"/api/doctor/appointments/{appt_id}", headers=docB_headers)
    assert docB_view_resp.status_code in [403, 404]
