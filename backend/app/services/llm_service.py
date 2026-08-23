import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field
from app.models.appointment import UrgencyLevel, AISummaryStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class PreVisitSummaryOutput(BaseModel):
    urgency: UrgencyLevel
    chief_complaint: str
    suggested_questions: List[str] = Field(..., min_length=1, max_length=5)


class MedicationItem(BaseModel):
    medicine: str
    dosage: str
    instructions: str


class PostVisitSummaryOutput(BaseModel):
    summary: str
    medication_schedule: List[MedicationItem] = []
    follow_up_steps: List[str] = []


class LLMProvider:
    """Base interface for LLM service providers."""
    async def generate_pre_visit_summary(self, symptoms: str) -> PreVisitSummaryOutput:
        raise NotImplementedError

    async def generate_post_visit_summary(self, clinical_notes: str, prescription: Optional[str] = None) -> PostVisitSummaryOutput:
        raise NotImplementedError


class GeminiLLMProvider(LLMProvider):
    """Google Gemini AI 1.5 Flash Provider for Pre and Post Visit Summaries."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

    async def _call_gemini_api(self, prompt: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.endpoint, json=payload)
            resp.raise_for_request()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No text generated from Gemini API.")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Empty response parts from Gemini API.")
            return parts[0].get("text", "")

    async def generate_pre_visit_summary(self, symptoms: str) -> PreVisitSummaryOutput:
        prompt = (
            f"You are a clinical AI triage assistant for the HealthY medical platform. "
            f"Analyze the following patient reported symptoms: '{symptoms}'.\n"
            f"Respond ONLY with a valid raw JSON object matching this schema:\n"
            f"{{\n"
            f'  "urgency": "Low" | "Medium" | "High",\n'
            f'  "chief_complaint": "Concise medical chief complaint",\n'
            f'  "suggested_questions": ["Question 1", "Question 2", "Question 3"]\n'
            f"}}\n"
            f"Do not include markdown code block formatting."
        )
        try:
            raw_response = await self._call_gemini_api(prompt)
            clean_json = raw_response.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            urgency_str = parsed.get("urgency", "Medium").capitalize()
            urgency = UrgencyLevel.High if urgency_str == "High" else UrgencyLevel.Low if urgency_str == "Low" else UrgencyLevel.Medium
            return PreVisitSummaryOutput(
                urgency=urgency,
                chief_complaint=parsed.get("chief_complaint", f"Patient presents with: {symptoms}"),
                suggested_questions=parsed.get("suggested_questions", [
                    "How long have you experienced these symptoms?",
                    "Have you noticed any worsening factors?",
                    "Are you currently taking any medications for relief?"
                ])
            )
        except Exception as e:
            logger.warning(f"Gemini API call failed ({str(e)}), falling back to intelligent mock triage.")
            return await MockLLMProvider().generate_pre_visit_summary(symptoms)

    async def generate_post_visit_summary(self, clinical_notes: str, prescription: Optional[str] = None) -> PostVisitSummaryOutput:
        prompt = (
            f"You are a compassionate clinical AI assistant for HealthY. "
            f"Translate the following doctor clinical notes and prescription into a clear, empathetic summary for the patient.\n"
            f"Clinical Notes: '{clinical_notes}'\n"
            f"Prescription: '{prescription or 'None'}'\n\n"
            f"Respond ONLY with a valid raw JSON object matching this schema:\n"
            f"{{\n"
            f'  "summary": "Empathetic patient-friendly summary of the visit and diagnosis",\n'
            f'  "medication_schedule": [\n'
            f'    {{"medicine": "Medicine Name", "dosage": "Dosage details", "instructions": "When/how to take"}}\n'
            f"  ],\n"
            f'  "follow_up_steps": ["Follow-up step 1", "Follow-up step 2"]\n'
            f"}}\n"
            f"Do not include markdown code block formatting."
        )
        try:
            raw_response = await self._call_gemini_api(prompt)
            clean_json = raw_response.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_json)
            meds = [
                MedicationItem(
                    medicine=m.get("medicine", "Prescribed Medication"),
                    dosage=m.get("dosage", "As directed"),
                    instructions=m.get("instructions", "Take as prescribed")
                )
                for m in parsed.get("medication_schedule", [])
            ]
            return PostVisitSummaryOutput(
                summary=parsed.get("summary", f"Summary of your visit: {clinical_notes}"),
                medication_schedule=meds,
                follow_up_steps=parsed.get("follow_up_steps", ["Take prescribed medications as scheduled.", "Rest and stay hydrated."])
            )
        except Exception as e:
            logger.warning(f"Gemini API post-visit call failed ({str(e)}), falling back to intelligent mock summary.")
            return await MockLLMProvider().generate_post_visit_summary(clinical_notes, prescription)


class MockLLMProvider(LLMProvider):
    """Intelligent deterministic provider for local development, testing, and offline execution."""

    async def generate_pre_visit_summary(self, symptoms: str) -> PreVisitSummaryOutput:
        symptoms_lower = symptoms.lower()
        if any(w in symptoms_lower for w in ["chest pain", "shortness of breath", "severe bleeding", "fainting", "stroke"]):
            urgency = UrgencyLevel.High
            questions = [
                "When did the severe symptoms begin?",
                "Are you experiencing radiation of pain to your jaw or arm?",
                "Do you have a history of cardiovascular or respiratory conditions?"
            ]
        elif any(w in symptoms_lower for w in ["fever", "cough", "vomiting", "headache", "nausea", "pain"]):
            urgency = UrgencyLevel.Medium
            questions = [
                "Have you noticed any specific triggers or morning patterns for these symptoms?",
                "Are these symptoms interfering with your daily routine or sleep?",
                "Are you currently taking any over-the-counter medications for relief?"
            ]
        else:
            urgency = UrgencyLevel.Low
            questions = [
                "How long have you been noticing these mild symptoms?",
                "Is this a routine wellness consultation or targeted follow-up?",
                "Do you have any specific health goals or concerns to discuss today?"
            ]

        chief_complaint = f"Patient presents with: {symptoms}"
        return PreVisitSummaryOutput(
            urgency=urgency,
            chief_complaint=chief_complaint,
            suggested_questions=questions
        )

    async def generate_post_visit_summary(self, clinical_notes: str, prescription: Optional[str] = None) -> PostVisitSummaryOutput:
        summary = (
            f"It was great seeing you today. We completed your consultation and evaluated your symptoms. "
            f"Doctor's Assessment: {clinical_notes}. Please follow the recommended care plan below."
        )
        medication_schedule = []
        if prescription:
            medication_schedule.append(
                MedicationItem(
                    medicine=prescription,
                    dosage="As directed by physician",
                    instructions="Take with water as instructed during consultation."
                )
            )

        follow_up_steps = [
            "Take prescribed medications regularly as directed.",
            "Maintain proper hydration and adequate rest.",
            "Schedule a follow-up consultation if symptoms persist or change."
        ]
        return PostVisitSummaryOutput(
            summary=summary,
            medication_schedule=medication_schedule,
            follow_up_steps=follow_up_steps
        )


def get_llm_provider() -> LLMProvider:
    """Factory returning configured LLM provider."""
    if settings.LLM_PROVIDER.lower() == "gemini" and settings.LLM_API_KEY:
        return GeminiLLMProvider(api_key=settings.LLM_API_KEY, model_name=settings.LLM_MODEL_NAME or "gemini-1.5-flash")
    return MockLLMProvider()
