# Real-Time Blood Availability & Donor Matching System ("Rakta Nidhi")

An enterprise-grade full-stack healthcare operations platform designed for real-time blood stock management, emergency request fulfillment, and intelligent donor suitability prioritization powered by **Random Forest Machine Learning** and **Mamdani Fuzzy Logic**.

---

## 🌟 Key Features

- **Real-Time Operational Dashboard**: High-level statistical metrics (donors, hospitals, emergency requests, stock availability, low-inventory alerts) with real-time WebSocket live updates.
- **Intelligent Donor Matching Pipeline**:
  - **Random Forest Model**: Predicts donor suitability scores based on age, past donation history, availability, and geographic proximity.
  - **Mamdani Fuzzy Logic Engine**: Calculates real-time clinical urgency priority scores based on request severity, required units, and donor proximity.
  - **Combined Ranking Algorithm**: Ranks potential ABO-compatible donors dynamically to ensure rapid emergency dispatch.
- **Entity Management & Directory**: Complete CRUD administration for **Hospitals**, **Doctors**, **Patients**, **Donors**, **Blood Inventory**, **Blood Requests**, and **Donation Records**.
- **Real-Time Event Streaming**: WebSockets broadcast live updates across active administrative sessions whenever inventory levels, emergency requests, or donor availability statuses change.
- **Robust Persistence & Fallback Caching**: PostgreSQL 18 asynchronous database engine (`SQLAlchemy` async) with fallback Redis caching.

---

## 🏗️ Architecture & Technology Stack

### Backend
- **Framework**: FastAPI (Async Python 3.14)
- **Database**: PostgreSQL 18 (`asyncpg` + `SQLAlchemy 2.0`)
- **Caching & Pub/Sub**: Redis (`redis.asyncio`)
- **Machine Learning**: `scikit-learn` (Random Forest Classifier)
- **Fuzzy Logic**: `scikit-fuzzy` (Mamdani Inference System)
- **Real-Time Communication**: WebSockets (`/ws/events`)

### Frontend
- **Interface**: HTML5, Vanilla JavaScript (ES Modules), Custom CSS Design System
- **Theme**: Premium healthcare administrative interface ("Rakta Nidhi")
- **Live Updates**: WebSocket event client

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI Endpoint Routers (Donors, Hospitals, Inventory, Matching, etc.)
│   │   ├── core/            # Database configuration, Redis client, Environment settings
│   │   ├── fuzzy/           # Mamdani Fuzzy Logic Prioritization Engine
│   │   ├── ml/              # Random Forest Donor Suitability Model & Training Pipeline
│   │   ├── models/          # SQLAlchemy Entity Schemas
│   │   ├── schemas/         # Pydantic Data Validation Schemas
│   │   ├── websocket/       # Real-Time WebSocket Connection Manager
│   │   └── main.py          # FastAPI Main Application & Static Server Mount
│   └── scripts/
│       ├── seed_data.py     # Database Population Script
│       └── verify_system.py # End-to-End Automated Verification Test Suite
├── frontend/
│   ├── css/
│   │   └── styles.css       # Platform Styling & Design Tokens
│   ├── js/
│   │   ├── api.js           # REST API Client Module
│   │   ├── app.js           # UI View Switcher & Event Handlers
│   │   └── websocket.js     # Real-Time WebSocket Event Subscriber
│   └── index.html           # Main Single-Page Application Interface
├── .env.example             # Template for Environment Configuration
├── .gitignore               # Git Ignore Rules
├── requirements.txt         # Python Project Dependencies
└── README.md                # Project Documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **PostgreSQL 18** (or 14+) running locally
- **Redis Server** (Optional; fallback PostgreSQL caching mode active if offline)

### 2. Environment Setup

Clone the repository and copy `.env.example` to `.env`:

```bash
git clone https://github.com/an-k-ur-06/FYP-RTBA-DMS.git
cd FYP-RTBA-DMS
cp .env.example .env
```

Edit `.env` with your PostgreSQL database credentials:

```env
DATABASE_URL=postgresql+asyncpg://postgres:6769@localhost:5432/blood_matching_system
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=supersecretkey
```

### 3. Install Dependencies

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Database Initialization & Data Seeding

Run the seed script to create PostgreSQL tables and populate initial operational data (Hospitals, Doctors, Patients, Donors, Inventory, Requests):

```bash
python -m backend.scripts.seed_data
```

### 5. Running the Application

Launch the server with Uvicorn:

```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:
- **Application Dashboard**: `http://localhost:8000/`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## 🧪 Verification Suite

Run the end-to-end automated verification script to validate all 20 system checkpoints:

```bash
python -m backend.scripts.verify_system
```

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
