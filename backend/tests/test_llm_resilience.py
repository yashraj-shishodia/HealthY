import pytest
from unittest.mock import patch
from app.models.appointment import UrgencyLevel
from app.services.llm_service import MockLLMProvider
from app.workers.tasks import process_pre_visit_summary_async


@pytest.mark.asyncio
async def test_llm_mock_provider_pre_and_post_visit_summaries():
    """Test deterministic MockLLMProvider pre-visit and post-visit summarization logic."""
    provider = MockLLMProvider()

    # 1. Pre-visit summary test for severe chest pain -> High urgency
    output_high = await provider.generate_pre_visit_summary("Patient reports severe chest pain and shortness of breath")
    assert output_high.urgency == UrgencyLevel.High
    assert len(output_high.suggested_questions) == 3

    # 2. Pre-visit summary test for mild cold -> Low urgency
    output_low = await provider.generate_pre_visit_summary("Mild runny nose and clear fluid")
    assert output_low.urgency == UrgencyLevel.Low
    assert len(output_low.suggested_questions) == 3

    # 3. Post-visit summary test
    post_output = await provider.generate_post_visit_summary(
        clinical_notes="Patient has acute bronchitis. Prescribed amoxicillin 500mg.",
        prescription="Amoxicillin 500mg 3x daily for 7 days"
    )
    assert "bronchitis" in post_output.summary
    assert len(post_output.medication_schedule) == 1
    assert len(post_output.follow_up_steps) == 3


@pytest.mark.asyncio
async def test_llm_failure_does_not_corrupt_appointment(async_client, db_session):
    """CRITICAL LLM FAULT ISOLATION TEST:
    Verify that if the LLM provider times out or throws an exception,
    the appointment remains valid in BOOKED state, pre_visit_summary_status becomes FAILED,
    and no unhandled exception breaks the system.
    """
    # Register Admin, Doctor & Patient
    admin_reg = {"email": "admin.llm@healthy.com", "password": "AdminPassword123!", "full_name": "Admin LLM", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.llm@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    doc_req = {
        "email": "dr.llm@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. LLM Failure Test",
        "specialisation": "Internal Medicine",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    doctor_id = doc_resp.json()["id"]

    patient_reg = {"email": "patient.llm@healthy.com", "password": "PatientPassword123!", "full_name": "Patient LLM", "role": "PATIENT"}
    await async_client.post("/api/auth/register", json=patient_reg)
    patient_login = await async_client.post("/api/auth/login", json={"email": "patient.llm@healthy.com", "password": "PatientPassword123!"})
    patient_headers = {"Authorization": f"Bearer {patient_login.json()['access_token']}"}

    # Mock LLM provider to throw an exception
    with patch("app.workers.tasks.get_llm_provider") as mock_get_provider:
        mock_provider = MockLLMProvider()
        mock_provider.generate_pre_visit_summary = Exception("Mock LLM Provider Timeout / API Error 500")
        mock_get_provider.return_value = mock_provider

        booking_payload = {
            "doctor_id": doctor_id,
            "appointment_date": "2026-08-24",
            "start_time": "09:00:00",
            "end_time": "09:30:00",
            "symptoms": "Severe fatigue and dizziness"
        }
        # Booking request must succeed with 201 Created
        resp = await async_client.post("/api/appointments", json=booking_payload, headers=patient_headers)
        assert resp.status_code == 201
        appt_id = resp.json()["id"]
        assert resp.json()["status"] == "BOOKED"

        # Await async business logic with mocked exception using db_session
        await process_pre_visit_summary_async(appt_id, db=db_session)

        # Check appointment status: record remains BOOKED, pre_visit_summary_status becomes FAILED
        detail_resp = await async_client.get(f"/api/appointments/{appt_id}", headers=patient_headers)
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["status"] == "BOOKED"
        assert data["pre_visit_summary_status"] == "FAILED"
