"""
Data models — in-memory storage (swap for a real DB in production).
All patient data lives in Flask session during a browser session, plus
a server-side in-memory store keyed by patient_id for demo purposes.
"""
from __future__ import annotations
import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Optional


# ── Default/Demo patient profile ──────────────────────────────────────────
DEFAULT_PATIENT: dict = {
    "id": "demo-001",
    "name": "Alex Johnson",
    "age": 54,
    "gender": "Male",
    "weight_kg": 88,
    "height_cm": 175,
    "blood_group": "O+",
    "allergies": ["Penicillin", "Sulfa drugs"],
    "current_medications": ["Metformin 500mg", "Amlodipine 5mg", "Aspirin 75mg"],
    "existing_conditions": ["Type 2 Diabetes", "Hypertension"],
    "family_history": ["Heart Disease (Father)", "Type 2 Diabetes (Mother)", "Hypertension (Sibling)"],
    "emergency_contact": {
        "name": "Sarah Johnson",
        "relation": "Spouse",
        "phone": "+1-555-0192",
    },
    "caregivers": [
        {"name": "Sarah Johnson", "relation": "Spouse", "access": "full"},
        {"name": "Dr. Michael Lee", "relation": "Primary Physician", "access": "full"},
    ],
    "created_at": datetime.now().isoformat(),
}


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0:
        return 0.0
    h_m = height_cm / 100
    return round(weight_kg / (h_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obese"


# ── Simulated wearable / health data generator ────────────────────────────
def generate_health_reading(patient: dict, anomaly: bool = False) -> dict:
    """
    Simulate a wearable device reading.
    When anomaly=True, inject a clinically significant out-of-range value
    to demonstrate the alert system.
    """
    base_glucose  = 130 if "Type 2 Diabetes" in patient.get("existing_conditions", []) else 95
    base_systolic = 138 if "Hypertension" in patient.get("existing_conditions", [])   else 118
    base_diastolic= 88  if "Hypertension" in patient.get("existing_conditions", [])   else 76

    hr      = random.randint(62, 88)
    systolic= base_systolic + random.randint(-8, 12)
    diastolic=base_diastolic + random.randint(-5, 8)
    glucose = base_glucose  + random.randint(-15, 30)
    spo2    = random.uniform(96, 99)
    temp    = round(random.uniform(36.4, 37.2), 1)
    steps   = random.randint(1800, 8500)
    sleep_h = round(random.uniform(5.5, 8.0), 1)
    stress  = random.randint(20, 65)

    if anomaly:
        pick = random.choice(["bp", "glucose", "hr"])
        if pick == "bp":
            systolic  = random.randint(185, 200)
            diastolic = random.randint(112, 125)
        elif pick == "glucose":
            glucose   = random.randint(260, 310)
        else:
            hr        = random.randint(125, 145)

    return {
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        "heart_rate": hr,
        "systolic_bp": systolic,
        "diastolic_bp": diastolic,
        "blood_glucose": glucose,
        "spo2": round(spo2, 1),
        "temperature": temp,
        "steps": steps,
        "sleep_hours": sleep_h,
        "stress_index": stress,
    }


def generate_health_trend(patient: dict, days: int = 7) -> list[dict]:
    """Return a list of daily health readings for trending charts."""
    trend = []
    for i in range(days):
        day_offset = days - 1 - i
        reading = generate_health_reading(patient, anomaly=(i == 1))
        reading["timestamp"] = (
            datetime.now() - timedelta(days=day_offset)
        ).strftime("%b %d")
        trend.append(reading)
    return trend


# ── Medication schedule ────────────────────────────────────────────────────
MEDICATION_SCHEDULE: list[dict] = [
    {
        "id": "med-001",
        "name": "Metformin 500mg",
        "frequency": "Twice daily",
        "times": ["08:00", "20:00"],
        "with_food": True,
        "adherence": 87,
        "next_dose": "Today 20:00",
        "refill_days": 12,
        "color": "#3b82d4",
    },
    {
        "id": "med-002",
        "name": "Amlodipine 5mg",
        "frequency": "Once daily",
        "times": ["08:00"],
        "with_food": False,
        "adherence": 94,
        "next_dose": "Tomorrow 08:00",
        "refill_days": 22,
        "color": "#7c5cd8",
    },
    {
        "id": "med-003",
        "name": "Aspirin 75mg",
        "frequency": "Once daily",
        "times": ["08:00"],
        "with_food": True,
        "adherence": 91,
        "next_dose": "Tomorrow 08:00",
        "refill_days": 18,
        "color": "#10b981",
    },
]


# ── Risk scoring helper ────────────────────────────────────────────────────
def compute_risk_score(patient: dict, reading: dict) -> dict:
    """
    Simple rule-based risk scorer — the AI supplements this with
    Watsonx.ai narrative analysis.
    Returns a score 0-100 and a label.
    """
    score = 0

    # Vitals
    if reading["systolic_bp"] > 160:    score += 25
    elif reading["systolic_bp"] > 140:  score += 15
    if reading["blood_glucose"] > 200:  score += 25
    elif reading["blood_glucose"] > 160:score += 12
    if reading["heart_rate"] > 110 or reading["heart_rate"] < 52: score += 15
    if reading["spo2"] < 93:            score += 20

    # Profile risk factors
    age = int(patient.get("age", 0))
    if age > 65:   score += 10
    elif age > 50: score += 5

    conditions = patient.get("existing_conditions", [])
    score += min(len(conditions) * 5, 20)

    family_hx = patient.get("family_history", [])
    score += min(len(family_hx) * 3, 15)

    score = min(score, 100)

    if score >= 70:
        label, color = "CRITICAL", "#ef4444"
    elif score >= 45:
        label, color = "HIGH", "#f97316"
    elif score >= 20:
        label, color = "MODERATE", "#eab308"
    else:
        label, color = "LOW", "#22c55e"

    return {"score": score, "label": label, "color": color}


# ── In-memory chat history ─────────────────────────────────────────────────
chat_history: list[dict] = []

def add_message(role: str, content: str):
    chat_history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M"),
    })
    # Keep last 40 messages in memory
    if len(chat_history) > 40:
        chat_history.pop(0)
