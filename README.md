# CareGuard AI — Chronic Disease Monitoring Agent

> **AI-powered health monitoring web application** built with Python Flask and IBM Watsonx.ai (Granite models).

---

## Features

| Feature | Description |
|---|---|
| **Health Dashboard** | Real-time vitals (HR, BP, Glucose, SpO2, Temp, Steps) with live Chart.js trends |
| **AI Chat** | Conversational health assistant powered by IBM Granite, context-aware of patient profile |
| **Risk Analysis** | Automatic risk scoring (LOW / MODERATE / HIGH / CRITICAL) with AI narrative |
| **Patient Profile** | Full medical profile: demographics, allergies, medications, conditions, family history, emergency contact |
| **Medication Reminders** | Adherence tracking, refill alerts, AI-powered medication interaction advice |
| **Care Team** | Family & caregiver profile management with role-based access |
| **Dark Mode** | Full light/dark theme toggle, persisted in `localStorage` |
| **Mobile Responsive** | Bootstrap 5, works on all screen sizes |

---

## Project Structure

```
chronic_disease_agent/
├── app.py                  ← Flask entry point & all routes
├── config.py               ← Environment config (reads .env)
├── agent_instructions.py   ← CUSTOMIZE AI behavior here
├── models.py               ← Data models, health simulators, risk scorer
├── watsonx_client.py       ← IBM Watsonx.ai / Granite integration
├── requirements.txt
├── .env.example            ← Copy to .env and fill in credentials
├── templates/
│   ├── base.html           ← Shared layout (navbar, footer, theme)
│   ├── dashboard.html      ← Main health dashboard
│   ├── chat.html           ← AI chat interface
│   ├── patient_profile.html← Patient information form
│   ├── medications.html    ← Medication tracker
│   ├── caregivers.html     ← Family / care team
│   └── error.html
└── static/
    ├── css/style.css       ← All styles (light + dark theme)
    └── js/app.js           ← Theme toggle, toasts, markdown renderer
```

---

## Quick Start (Local Development)

### 1. Prerequisites

- Python 3.10 or higher
- An [IBM Cloud account](https://cloud.ibm.com/)
- A Watsonx.ai project with the Granite model enabled

### 2. Clone / copy the project

```bash
cd chronic_disease_agent
```

### 3. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
IBM_API_KEY=5TmU_DzDNr5HLEBFJ2HT4m7ctMClHQrOV2-oeBeVwKNh
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_WATSONX_PROJECT_ID=7b457073-aa3c-4f7d-8379-cd15734d809b
FLASK_SECRET_KEY=change_this_to_a_random_string
```

#### How to get IBM credentials

1. Log in to [IBM Cloud Console](https://cloud.ibm.com/)
2. Go to **Manage → Access (IAM) → API Keys** → Create an API key
3. Open [IBM Watsonx.ai](https://dataplatform.cloud.ibm.com/)
4. Create a new project → copy the **Project ID** from the project settings

### 6. Run the application

```bash
UV run app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Customizing the AI Agent

All AI behavior is configured in **`agent_instructions.py`**:

```python
# Change the agent's name and tone
AGENT_NAME = "CareGuard AI"
AGENT_TONE = "empathetic, professional, clear, and encouraging"

# Enable/disable disease specializations
SPECIALIZATIONS = {
    "diabetes":    True,
    "hypertension": True,
    "heart_disease": True,
    ...
}

# Adjust alert thresholds
ALERT_THRESHOLDS = {
    "systolic_bp_high": 180,   # mmHg
    "blood_glucose_high": 250, # mg/dL
    ...
}
```

No restart required if you use Flask's debug mode — just save and refresh.

---

## Changing the Granite Model

In `config.py`, update `GRANITE_MODEL_ID`:

```python
GRANITE_MODEL_ID: str = "ibm/granite-3-3-8b-instruct"
# Other options:
# "ibm/granite-13b-chat-v2"
# "ibm/granite-3-8b-instruct"
```

---

## Deployment on IBM Cloud Code Engine

### 1. Create a `Procfile`

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

### 2. Create a `runtime.txt`

```
python-3.11.x
```

### 3. Deploy via IBM Cloud CLI

```bash
# Install IBM Cloud CLI and Code Engine plugin
ibmcloud plugin install code-engine

# Log in
ibmcloud login --apikey YOUR_API_KEY -r us-south

# Target a resource group
ibmcloud target -g Default

# Create or select a Code Engine project
ibmcloud ce project create --name careguard-ai
# or
ibmcloud ce project select --name careguard-ai

# Create the application from source
ibmcloud ce app create \
  --name careguard-ai \
  --image us.icr.io/your-namespace/careguard-ai:latest \
  --registry-secret my-registry-secret \
  --env IBM_API_KEY=5TmU_DzDNr5HLEBFJ2HT4m7ctMClHQrOV2-oeBeVwKNh \
  --env IBM_WATSONX_PROJECT_ID=your_project_id \
  --env IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env FLASK_SECRET_KEY=your_secret \
  --port 5000 \
  --min-scale 1
```

### 4. Deploy via IBM Cloud Foundry (alternative)

```bash
# manifest.yml
applications:
- name: careguard-ai
  memory: 512M
  instances: 1
  buildpack: python_buildpack
  command: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
  env:
    IBM_API_KEY: 5TmU_DzDNr5HLEBFJ2HT4m7ctMClHQrOV2-oeBeVwKNh
    IBM_WATSONX_PROJECT_ID: 7b457073-aa3c-4f7d-8379-cd15734d809b
    IBM_WATSONX_URL: https://us-south.ml.cloud.ibm.com
    FLASK_SECRET_KEY: your_secret
```

```bash
ibmcloud cf push
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `IBM_API_KEY` | ✅ | — | IBM Cloud API Key for Watsonx.ai auth |
| `IBM_WATSONX_URL` | ✅ | `https://us-south.ml.cloud.ibm.com` | Regional Watsonx endpoint |
| `IBM_WATSONX_PROJECT_ID` | ✅ | — | Your Watsonx.ai project ID |
| `FLASK_SECRET_KEY` | ✅ | `dev-secret-change-me` | Flask session signing key |
| `FLASK_DEBUG` | ❌ | `False` | Enable debug mode |
| `APP_PORT` | ❌ | `5000` | Server port |

---

## Architecture Overview

```
Browser ──HTTPS──► Flask App
                     │
                     ├── /dashboard      → renders dashboard.html + simulated vitals
                     ├── /chat           → renders chat.html
                     ├── /api/chat       → Watsonx.ai Granite ← enriched prompt
                     ├── /api/analyze    → full AI health analysis
                     ├── /api/patient    → save patient profile to session
                     └── /api/health-reading → simulated wearable data

Watsonx.ai:
  system_prompt = agent_instructions.build_system_prompt(patient)
  user_message  = chat message + latest vitals
  model         = ibm/granite-3-3-8b-instruct
```

---

## Security Notes

- **Never commit `.env`** — it is already in `.gitignore`
- For production, use IBM Secrets Manager or environment variable injection
- The current implementation uses Flask sessions (server-side cookie); for multi-user production use replace with a proper database (PostgreSQL, Cloudant, etc.)
- Add HTTPS (TLS) termination at the load balancer or IBM Cloud proxy layer

---

## License

MIT License — for educational and demonstration purposes.  
This application does **not** constitute medical advice.
