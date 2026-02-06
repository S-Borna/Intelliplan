# 🧠 Intelliplan — AI-Powered Staffing Operations Platform

En intelligent plattform för bemanningsföretag som fångar kundbehov, bedömer genomförbarhet, koordinerar åtgärder och vägleder beslut — allt drivet av AI.

---

## ✨ Funktioner

| Funktion | Beskrivning |
|----------|-------------|
| 🎯 **Smart Intake** | AI-driven kundförfrågningshantering med kontextberikning, automatisk kategorisering och komplexitetsbedömning |
| 📊 **Genomförbarhetsanalys** | Automatisk utvärdering av tillgänglighet, kompetens, compliance, budget och tidslinje |
| 👥 **Konsultmatchning** | AI-baserad matchning mot 60+ kompetenser i 8 kategorier med poängsättning |
| 📌 **Tilldelningsflöde** | Komplett livscykel: tilldela → skicka till konsult → godkänn/avböj med notiser i varje steg |
| 🔔 **Notifikationssystem** | Realtidsnotiser till handläggare och kunder vid statusändringar |
| 🔐 **Autentisering** | Rollbaserad åtkomst (admin, handläggare, kund) med token-baserad auth |
| 🏢 **Kundportal** | Kunderna kan skicka förfrågningar och följa status i realtid |
| ⚡ **Koordinationsmotor** | Automatiserade arbetsflöden med åtgärdsplaner och tidslinje |
| ✅ **Compliance Engine** | Automatiska kontroller mot regelverk och avtal |

---

## 🏗️ Arkitektur

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (SPA)                        │
│  ┌────────────────┐  ┌─────────────────────────────────┐ │
│  │ Kundportal     │  │ Handläggardashboard             │ │
│  │ • Ny förfrågan │  │ • KPI-översikt                  │ │
│  │ • Mina ärenden │  │ • Förfrågningskö                │ │
│  │ • Notiser      │  │ • Konsultmatchning & tilldelning│ │
│  └────────────────┘  │ • Genomförbarhetsanalys          │ │
│                      │ • Tidslinje & notiser            │ │
│   🔐 Login           └─────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────┘
                           │ REST API
┌──────────────────────────▼───────────────────────────────┐
│                   Backend (FastAPI)                       │
│                                                          │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐  │
│  │ AI Engine   │ │ Coordinator  │ │ Compliance Engine │  │
│  │ • Taxonomi  │ │ • Åtgärder   │ │ • Regelkontroll   │  │
│  │ • Matchning │ │ • Tidslinje  │ │ • Validering      │  │
│  │ • Scoring   │ │ • Tilldelning│ │ • Audit trail     │  │
│  └─────────────┘ └──────────────┘ └───────────────────┘  │
│                                                          │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────┐  │
│  │ Auth Router │ │ Notis Router │ │ Feasibility       │  │
│  │ • Login     │ │ • Push       │ │ • 5 dimensioner   │  │
│  │ • Register  │ │ • Polling    │ │ • Konfidensgrad   │  │
│  │ • Roller    │ │ • Läskvitto  │ │ • Rekommendation  │  │
│  └─────────────┘ └──────────────┘ └───────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │
                  ┌────────▼────────┐
                  │  SQLite (SQLAlchemy ORM)  │
                  └─────────────────┘
```

---

## 🚀 Quick Start

```bash
# 1. Klona repot
git clone https://github.com/S-Borna/Intelliplan.git
cd Intelliplan

# 2. Skapa virtuell miljö
python3 -m venv .venv
source .venv/bin/activate

# 3. Installera beroenden
pip install -r requirements.txt

# 4. Starta servern
uvicorn backend.main:app --reload --port 8000

# 5. Öppna i webbläsaren
open http://localhost:8000
```

---

## 🔑 Demokonton

| Roll | E-post | Lösenord |
|------|--------|----------|
| Admin | `admin@intelliplan.se` | `admin123` |
| Handläggare | `handler@intelliplan.se` | `handler123` |
| Handläggare | `marcus@intelliplan.se` | `handler123` |
| Kund (Volvo) | `anna.lindstrom@volvo.com` | `kund123` |
| Kund (Spotify) | `erik.j@spotify.com` | `kund123` |
| Kund (SEB) | `maria.karlsson@seb.se` | `kund123` |

---

## 📌 Tilldelningsflöde

```
Handläggare klickar "Tilldela konsult"
        │
        ▼
  Status: "Skickad till konsult"
  📩 Notis → handläggare & kund
        │
        ├──── Konsult godkänner ────▶ Status: "Godkänd ✓"
        │                            📩 Notis → alla parter
        │                            ✅ Förfrågan stängs om alla platser fyllda
        │
        └──── Konsult avböjer ──────▶ Status: "Avböjd"
                                      📩 Notis → handläggare & kund
                                      🔄 Konsult blir tillgänglig igen
```

---

## 🧪 API-endpoints

| Metod | Endpoint | Beskrivning |
|-------|----------|-------------|
| `POST` | `/api/auth/login` | Logga in |
| `POST` | `/api/auth/register` | Registrera användare |
| `GET` | `/api/auth/me` | Aktuell användare |
| `GET` | `/api/requests` | Lista förfrågningar |
| `POST` | `/api/requests` | Skapa förfrågan (AI-analys körs automatiskt) |
| `GET` | `/api/requests/{id}` | Detalj med matchning, bedömning, tilldelningar |
| `POST` | `/api/requests/{id}/assign/{consultant_id}` | Tilldela konsult |
| `PATCH` | `/api/requests/{id}/assignments/{aid}/approve` | Godkänn tilldelning |
| `PATCH` | `/api/requests/{id}/assignments/{aid}/reject` | Avböj tilldelning |
| `GET` | `/api/notifications` | Användarens notiser |
| `GET` | `/api/consultants` | Lista konsulter |
| `GET` | `/api/customers` | Lista kunder |
| `GET` | `/api/dashboard/stats` | KPI-statistik |
| `GET` | `/docs` | Swagger API-dokumentation |

---

## 🛠️ Tech Stack

| Lager | Teknologi |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Frontend** | Vanilla JS (SPA), HTML5, CSS3 med glassmorphism-design |
| **Databas** | SQLite (utbytbar mot PostgreSQL) |
| **AI** | Regelbaserad motor med taxonomi för 60+ kompetenser |
| **Auth** | Token-baserad autentisering med rollhantering |

---

## 📁 Projektstruktur

```
Intelliplan/
├── backend/
│   ├── main.py              # FastAPI app, routing, lifespan
│   ├── models.py            # SQLAlchemy ORM-modeller
│   ├── schemas.py           # Pydantic request/response-scheman
│   ├── database.py          # Databasanslutning
│   ├── config.py            # Konfiguration
│   ├── seed_data.py         # Demodata (kunder, konsulter, användare)
│   ├── routers/
│   │   ├── auth.py          # Autentisering & sessioner
│   │   ├── requests.py      # Förfrågningar, tilldelning, godkännande
│   │   ├── notifications.py # Notiser med hjälpfunktioner
│   │   ├── customers.py     # Kundhantering
│   │   └── dashboard.py     # KPI-statistik
│   └── services/
│       ├── ai_engine.py     # AI-analys, matchning, scoring
│       ├── feasibility.py   # Genomförbarhetsanalys (5 dimensioner)
│       ├── coordinator.py   # Åtgärdsplaner, tilldelning, workflow
│       └── compliance.py    # Regelefterlevnad
├── frontend/
│   ├── index.html           # SPA med login, dashboard, portal
│   ├── css/styles.css       # Premium dark glassmorphism-tema
│   └── js/app.js            # Klientlogik, API-anrop, rendering
├── requirements.txt
└── .gitignore
```

---

## 📜 Licens

MIT
