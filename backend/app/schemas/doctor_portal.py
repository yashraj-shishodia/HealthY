import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MedicationInstructionItem(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int = Field(7, ge=1, le=90)


class CompleteAppointmentRequest(BaseModel):
    doctor_notes: str = Field(..., min_length=1, max_length=5000)
    prescription: Optional[str] = None
    medication_instructions: List[MedicationInstructionItem] = []

    model_config = ConfigDict(from_attributes=True)
