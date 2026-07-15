"""
CareGuard AI — Flask Application Entry Point
==========================================
Run: python app.py  (development)
Run: gunicorn -w 4 -b 0.0.0.0:5000 app:app  (production)
"""
from __future__ import annotations
import json
import copy
from flask import (
    Flask, render_template, request,
    jsonify, session, redirect, url_for, flash,
)
from config import Config
from models import (
    DEFAULT_PATIENT, MEDICATION_SCHEDULE,
    generate_health_reading, generate_health_trend,
    compute_bmi, bmi_category, compute_risk_score,
    chat_history, add_message,
)
from agent_instructions import build_system_prompt
from watsonx_client import query_watsonx

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY


# ── Helpers ────────────────────────────────────────────────────────────────
def get_patient() -> dict:
    """Return patient from session, falling back to default demo patient."""
    return session.get("patient", copy.deepcopy(DEFAULT_PATIENT))


def save_patient(patient: dict):
    session["patient"] = patient
    session.modified = True


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    patient  = get_patient()
    reading  = generate_health_reading(patient, anomaly=False)
    trend    = generate_health_trend(patient, days=7)
    risk     = compute_risk_score(patient, reading)
    bmi      = compute_bmi(patient["weight_kg"], patient["height_cm"])
    bmi_cat  = bmi_category(bmi)
    meds     = MEDICATION_SCHEDULE

    # Serialize trend for chart.js
    trend_labels   = [r["timestamp"] for r in trend]
    trend_glucose  = [r["blood_glucose"] for r in trend]
    trend_systolic = [r["systolic_bp"] for r in trend]
    trend_hr       = [r["heart_rate"] for r in trend]

    return render_template(
        "dashboard.html",
        patient=patient,
        reading=reading,
        risk=risk,
        bmi=bmi,
        bmi_cat=bmi_cat,
        meds=meds,
        trend_labels=json.dumps(trend_labels),
        trend_glucose=json.dumps(trend_glucose),
        trend_systolic=json.dumps(trend_systolic),
        trend_hr=json.dumps(trend_hr),
        page="dashboard",
    )


@app.route("/chat", methods=["GET"])
def chat():
    patient = get_patient()
    return render_template(
        "chat.html",
        patient=patient,
        chat_history=chat_history,
        page="chat",
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """AJAX endpoint — receives user message, queries Watsonx, returns JSON."""
    data    = request.get_json(force=True)
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    patient       = get_patient()
    reading       = generate_health_reading(patient)
    system_prompt = build_system_prompt(patient)

    # Enrich user message with latest vitals context
    enriched = (
        f"{message}\n\n"
        f"[Latest vitals — auto-injected by wearable sensor]\n"
        f"HR: {reading['heart_rate']} bpm | BP: {reading['systolic_bp']}/{reading['diastolic_bp']} mmHg | "
        f"Glucose: {reading['blood_glucose']} mg/dL | SpO2: {reading['spo2']}% | Temp: {reading['temperature']}°C"
    )

    add_message("user", message)
    reply = query_watsonx(system_prompt, enriched)
    add_message("assistant", reply)

    return jsonify({
        "reply": reply,
        "timestamp": chat_history[-1]["timestamp"],
        "reading": reading,
    })


@app.route("/api/health-reading")
def api_health_reading():
    """Return a fresh simulated health reading (used for live dashboard refresh)."""
    patient = get_patient()
    anomaly = request.args.get("anomaly", "false").lower() == "true"
    reading = generate_health_reading(patient, anomaly=anomaly)
    risk    = compute_risk_score(patient, reading)
    return jsonify({"reading": reading, "risk": risk})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Trigger a full AI health analysis with the latest vitals."""
    patient       = get_patient()
    reading       = generate_health_reading(patient)
    risk          = compute_risk_score(patient, reading)
    system_prompt = build_system_prompt(patient)

    prompt = (
        f"Perform a comprehensive health analysis for this patient.\n\n"
        f"Current Vitals:\n"
        f"- Heart Rate: {reading['heart_rate']} bpm\n"
        f"- Blood Pressure: {reading['systolic_bp']}/{reading['diastolic_bp']} mmHg\n"
        f"- Blood Glucose: {reading['blood_glucose']} mg/dL\n"
        f"- SpO2: {reading['spo2']}%\n"
        f"- Temperature: {reading['temperature']}°C\n"
        f"- Daily Steps: {reading['steps']}\n"
        f"- Sleep: {reading['sleep_hours']} hours\n"
        f"- Stress Index: {reading['stress_index']}/100\n\n"
        f"Pre-computed Risk Score: {risk['score']}/100 ({risk['label']})\n\n"
        f"Please provide:\n"
        f"1. Risk level assessment\n"
        f"2. Key observations\n"
        f"3. Personalized recommendations (diet, exercise, medication adherence)\n"
        f"4. Early warning signs to watch for\n"
        f"5. Motivational message\n"
    )

    analysis = query_watsonx(system_prompt, prompt)
    add_message("assistant", f"📊 **AI Health Analysis**\n\n{analysis}")
    return jsonify({"analysis": analysis, "reading": reading, "risk": risk})


@app.route("/patient-profile", methods=["GET"])
def patient_profile():
    patient = get_patient()
    bmi     = compute_bmi(patient["weight_kg"], patient["height_cm"])
    bmi_cat = bmi_category(bmi)
    return render_template(
        "patient_profile.html",
        patient=patient,
        bmi=bmi,
        bmi_cat=bmi_cat,
        page="profile",
    )


@app.route("/api/patient", methods=["POST"])
def api_update_patient():
    """Save updated patient profile from the form."""
    form = request.get_json(force=True)
    patient = get_patient()

    # Scalar fields
    for field in ["name", "age", "gender", "weight_kg", "height_cm", "blood_group"]:
        if field in form:
            patient[field] = form[field]

    # List fields (comma-separated strings in form)
    for list_field in ["allergies", "current_medications", "existing_conditions", "family_history"]:
        if list_field in form:
            raw = form[list_field]
            if isinstance(raw, list):
                patient[list_field] = [x.strip() for x in raw if x.strip()]
            else:
                patient[list_field] = [x.strip() for x in str(raw).split(",") if x.strip()]

    # Emergency contact
    if "emergency_contact" in form:
        ec = form["emergency_contact"]
        patient["emergency_contact"] = {
            "name":     ec.get("name", ""),
            "relation": ec.get("relation", ""),
            "phone":    ec.get("phone", ""),
        }

    save_patient(patient)
    return jsonify({"status": "saved", "patient": patient})


@app.route("/medications")
def medications():
    patient = get_patient()
    return render_template(
        "medications.html",
        patient=patient,
        meds=MEDICATION_SCHEDULE,
        page="medications",
    )


@app.route("/api/medication-reminder", methods=["POST"])
def api_medication_reminder():
    """Ask AI for personalized medication adherence advice."""
    patient       = get_patient()
    system_prompt = build_system_prompt(patient)
    meds_str      = "\n".join(f"- {m['name']} ({m['frequency']}) — Adherence: {m['adherence']}%" for m in MEDICATION_SCHEDULE)

    prompt = (
        f"The patient's current medication schedule:\n{meds_str}\n\n"
        f"Provide personalized medication adherence tips, potential interactions to watch for "
        f"(given known allergies: {', '.join(patient.get('allergies', []) or ['None'])}), "
        f"and strategies to improve adherence for any medication below 90%."
    )

    advice = query_watsonx(system_prompt, prompt)
    return jsonify({"advice": advice})


@app.route("/caregivers")
def caregivers():
    patient = get_patient()
    return render_template(
        "caregivers.html",
        patient=patient,
        caregivers=patient.get("caregivers", []),
        page="caregivers",
    )


@app.route("/api/reset-demo")
def api_reset_demo():
    """Reset session to default demo patient."""
    session.clear()
    return jsonify({"status": "reset"})


# ── Error handlers ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template("error.html", code=500, message="Internal server error"), 500


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
