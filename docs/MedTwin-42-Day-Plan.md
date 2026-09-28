# MedTwin: 42-Day Build Plan

- 37 build days + 5 report days, about 6 hours per day.
- Rest one day after every 6 working days (not counted).
- 86 features: 62 Must (M), 17 Should (S), 7 Nice (N).

**Daily routine:** read the day's goal (15 min) → build (about 5 h) → tests + check "Done when" (30 min) → Git commit, 1–2 screenshots, 3–4 lines of notes (15 min).

---

## 1. Feature checklist

### 1. Accounts
- [ ] 1.1 Login / logout with JWT (M)
- [ ] 1.2 Roles: Admin, Doctor, Nurse (M)
- [ ] 1.3 Role-based permissions (M)
- [ ] 1.4 Staff account management by Admin (S)
- [ ] 1.5 Audit log (N)

### 2. Hospital core
- [ ] 2.1 Units: ICU, Ward, ED (M)
- [ ] 2.2 Beds with status and map position (M)
- [ ] 2.3 Patients (M)
- [ ] 2.4 Admit / transfer / discharge (M)
- [ ] 2.5 Vital-sign readings (M)
- [ ] 2.6 Emergency arrivals with triage 1–5 (M)
- [ ] 2.7 Patient detail API (M)
- [ ] 2.8 Patient search and filters (S)

### 3. Equipment
- [ ] 3.1 Device register (M)
- [ ] 3.2 Device status (M)
- [ ] 3.3 Telemetry readings (M)
- [ ] 3.4 Maintenance log (S)

### 4. Simulator
- [ ] 4.1 Live simulation with adjustable speed (M)
- [ ] 4.2 Poisson arrivals with hourly/daily patterns (M)
- [ ] 4.3 Length of stay and discharges (M)
- [ ] 4.4 Vitals with deteriorating patients (M)
- [ ] 4.5 Equipment telemetry with injected faults (M)
- [ ] 4.6 History generator (M)
- [ ] 4.7 Calibration from real statistics, sources recorded (S)
- [ ] 4.8 Simulator controls: API + Admin screen (S)

### 5. Real-time
- [ ] 5.1 WebSocket connection (M)
- [ ] 5.2 Live messages: beds, vitals, alerts, equipment (M)
- [ ] 5.3 Redis message layer (M)
- [ ] 5.4 Automatic reconnection (S)

### 6. Alerts
- [ ] 6.1 Rule-based alerts (M)
- [ ] 6.2 ML-based alerts (M)
- [ ] 6.3 Severity levels (M)
- [ ] 6.4 Acknowledge / resolve with who and when (M)
- [ ] 6.5 De-duplication (M)
- [ ] 6.6 Toast and sound for critical alerts (S)
- [ ] 6.7 Admin-editable thresholds (N)

### 7A. ICU forecast
- [ ] 7A.1 Forecast 6/12/24/48/72 h ahead (M)
- [ ] 7A.2 Gradient Boosting with lag and time features (M)
- [ ] 7A.3 Compare with baseline and Prophet: MAE, RMSE (M)
- [ ] 7A.4 Hourly re-prediction in the app (M)
- [ ] 7A.5 Uncertainty band (N)

### 7B. Patient risk (research core)
- [ ] 7B.1 Logistic Regression, Random Forest, XGBoost compared (M)
- [ ] 7B.2 Trained on real data (PhysioNet 2019; eICU if approved) (M)
- [ ] 7B.3 NEWS2 baseline (M)
- [ ] 7B.4 AUROC, high-risk recall, confusion matrix (M)
- [ ] 7B.5 SHAP explanations (M)
- [ ] 7B.6 Unseen-hospital experiment (M)
- [ ] 7B.7 Fine-tuning / federated fix for the drop (S)
- [ ] 7B.8 Live risk scoring on new vitals (M)

### 7C. Equipment anomaly
- [ ] 7C.1 Isolation Forest (M)
- [ ] 7C.2 Compare with fixed thresholds (M)
- [ ] 7C.3 Precision / recall on injected faults (M)
- [ ] 7C.4 AI4I 2020 experiments (S)

### 8. Frontend
- [ ] 8.1 Login and role-aware navigation (M)
- [ ] 8.2 SVG floor map (M)
- [ ] 8.3 Live bed colours (M)
- [ ] 8.4 Bed side panel with risk + SHAP (M)
- [ ] 8.5 Dashboard KPIs and risk distribution (M)
- [ ] 8.6 ICU forecast chart (M)
- [ ] 8.7 Equipment list page (M)
- [ ] 8.8 Alerts page, alert detail, bell (M)
- [ ] 8.9 Responsive layout (N)
- [ ] 8.10 Patient forms: admit, vitals, transfer, discharge, ED arrival (M)
- [ ] 8.11 Patient list + full patient page (M)
- [ ] 8.12 Admin screens: staff accounts, alert thresholds (S)
- [ ] 8.13 Maintenance actions on equipment (S)
- [ ] 8.14 Emergency queue screen (M)
- [ ] 8.15 Equipment detail page + add/edit device form (S)
- [ ] 8.16 Hospital setup screen: units and beds (S)
- [ ] 8.17 Profile and change password (S)
- [ ] 8.18 System states: 403, 404, loading, empty, connection lost, session expired (M)
- [ ] 8.19 Audit log screen (N)

### 9. What-if simulation
- [ ] 9.1 Snapshot of current state (M)
- [ ] 9.2 SimPy engine, 48–72 h forward (M)
- [ ] 9.3 Scenarios: surge, beds, equipment out of service (M)
- [ ] 9.4 50 runs, averaged (M)
- [ ] 9.5 Scenario vs. baseline chart and summary (M)
- [ ] 9.6 Save and compare scenarios (N)

### 10. Analytics
- [ ] 10.1 Historical trends (S)
- [ ] 10.2 Model performance page (M)
- [ ] 10.3 CSV export (N)

### 11. Quality and delivery
- [ ] 11.1 Git repository, regular commits (M)
- [ ] 11.2 Backend tests (M)
- [ ] 11.3 Seed script (M)
- [ ] 11.4 Docker Compose (S)
- [ ] 11.5 User evaluation (S)

---

## 2. Screens (30)

| # | Screen | Who | Features | Day |
|---|---|---|---|---|
| S1 | Login | All | 8.1 | 16 |
| S2 | App shell (menu, Live indicator, alert bell, toasts) | All | 8.1, 8.8 | 16, 20 |
| S3 | Profile / change password | All | 8.17 | 16 |
| S4 | System states (403, 404, loading, empty, connection lost, session expired) | All | 8.18 | 16–17 |
| S5 | Hospital map | All | 8.2, 8.3 | 17–18 |
| S6 | Bed side panel | All | 8.4 | 18, 30 |
| S7 | Patient list | All | 8.11 | 18 |
| S8 | Patient page (overview, vitals, risk + SHAP + NEWS2, admissions, alerts) | All | 8.11 | 18, 30 |
| S9 | Register and admit form | Nurse, Admin | 8.10 | 19 |
| S10 | Record vitals form | Nurse | 8.10 | 19 |
| S11 | Transfer form | Doctor, Nurse | 8.10 | 19 |
| S12 | Discharge form | Doctor | 8.10 | 19 |
| S13 | Emergency queue | All | 8.14 | 20 |
| S14 | Log emergency arrival form | Nurse, Admin | 8.10 | 20 |
| S15 | Alerts page | All | 8.8 | 20 |
| S16 | Alert detail panel | All | 8.8 | 20 |
| S17 | Dashboard | All | 8.5, 8.6 | 21, 30 |
| S18 | Equipment list | All | 8.7 | 21 |
| S19 | Equipment detail + maintenance | All (actions: Admin) | 8.13, 8.15 | 21 |
| S20 | Add / edit device form | Admin | 8.15 | 21 |
| S21 | What-if builder and results | Admin | 9.5 | 33 |
| S22 | Saved scenarios | Admin | 9.6 | 33 |
| S23 | Trends + CSV export | Doctor, Admin | 10.1, 10.3 | 34–35 |
| S24 | Model performance | Doctor, Admin | 10.2 | 34 |
| S25 | Hospital setup (units and beds) | Admin | 8.16 | 22 |
| S26 | Staff accounts | Admin | 8.12 | 34 |
| S27 | Alert thresholds | Admin | 8.12 | 34 |
| S28 | Simulator controls | Admin | 4.8 | 33 |
| S29 | Audit log | Admin | 8.19 | 34 |
| S30 | Django admin (behind the scenes) | Admin / developer | — | 3 onward |

No "forgot password" screen: the Admin resets passwords from S26.

---

## 3. Day-by-day plan

### Week 1: Setup and backend foundation

| Day | Work | Features | Done when |
|---|---|---|---|
| 1 | Install tools; Git repo; folder structure; `.gitignore`; Python venv | 11.1 | Repo with structure, first commit |
| 2 | Django project + PostgreSQL (`.env` for secrets); DRF; empty apps; Next.js + TypeScript + Tailwind | 11.1 | `runserver` and `npm run dev` work; Django admin opens |
| 3 | Custom user model with role (before first migration); JWT login, refresh, logout | 1.1, 1.2 | Login through the API returns a token |
| 4 | Permission classes; staff management endpoints; change-password and reset-password endpoints; `AuditLog`; tests | 1.3, 1.4, 1.5, 8.17 (API) | Nurse gets 403 on Admin endpoints; tests pass |
| 5 | `Unit`, `Bed` (with `map_x`/`map_y`), `Patient`; Django admin | 2.1, 2.2, 2.3 | Units, beds, patients created in admin |
| 6 | `Admission`, `VitalReading`, `EmergencyArrival`; service functions `admit_patient()`, `transfer_patient()`, `discharge_patient()`; tests | 2.4, 2.5, 2.6 | Admit → bed occupied; discharge → bed free; tests pass |

### Week 2: APIs, equipment, simulator, real-time

| Day | Work | Features | Done when |
|---|---|---|---|
| 7 | Hospital APIs; patient detail; search and filters; emergency queue endpoint; unit/bed add-edit endpoints | 2.7, 2.8 | `/api/patients/?unit=ICU` and `/api/patients/5/` work |
| 8 | `Equipment`, `EquipmentReading`, `MaintenanceLog` + APIs (incl. add/edit device); `seed_hospital` command | 3.1–3.4, 11.3 | One command builds the demo hospital |
| 9 | `run_simulator` with clock and `--speed`; Poisson arrivals; length of stay; discharges (using service functions) | 4.1, 4.2, 4.3 | Beds fill and empty on their own |
| 10 | Vitals random walk with ~10% deteriorating; telemetry with injected faults (log fault start times) | 4.4, 4.5 | Deterioration visible in data; faults logged |
| 11 | `generate_history --months 6`; calibrate from eICU demo / papers (record sources); simulator control API | 4.6, 4.7, 4.8 (API) | **Checkpoint 1: simulator complete** |
| 12 | Redis in Docker; Channels + Daphne; `asgi.py`; `HospitalConsumer` | 5.1 (backend), 5.3 | Test client connects and gets a message |

### Week 3: Live messages, alerts, frontend start

| Day | Work | Features | Done when |
|---|---|---|---|
| 13 | Send messages from service functions; one message format | 5.2 | Test client prints live updates |
| 14 | `Alert` model; rules; severities; de-duplication | 6.1, 6.3, 6.5 | One deteriorating patient → exactly one alert |
| 15 | Acknowledge / resolve; `AlertThreshold`; alerts over WebSocket; tests | 6.4, 6.7 | Alerts arrive live and can be acknowledged; tests pass |
| 16 | App shell; login; role menu; profile + change password; 403/404/loading/empty states; session expiry | 8.1, 8.17, 8.18 | Browser login works; menu differs by role |
| 17 | API client with JWT; WebSocket hook with reconnection + connection-lost banner; static SVG map | 5.1 (frontend), 5.4, 8.18, 8.2 | Map shows correct bed colours on load |
| 18 | Live bed colours; bed side panel; patient list; basic patient page | 8.3, 8.4 (part 1), 8.11 (part 1) | Beds change live; panel and patient pages work |

### Week 4: Frontend completion, ML start

| Day | Work | Features | Done when |
|---|---|---|---|
| 19 | Forms: register and admit, record vitals, transfer, discharge (with role checks) | 8.10 | Admit a patient from the browser |
| 20 | Emergency queue + arrival form; alerts page, alert detail, bell; toasts and sound | 8.14, 8.10, 8.8, 6.6 | Critical alert pops up and can be acknowledged |
| 21 | Dashboard KPIs + risk chart; equipment list, detail, maintenance actions, add/edit device | 8.5, 8.7, 8.13, 8.15 | KPIs live; device can be put into maintenance |
| 22 | Hospital setup screen; full manual test of every screen as each role | 8.16 | **Checkpoint 2: full live frontend.** Admit a patient, enter low SpO₂, bed turns red with alert |
| 23 | ICU forecast notebook: features, time split, GBM vs. baseline vs. Prophet, quantile band | 7A.1, 7A.2, 7A.3, 7A.5 | MAE/RMSE table; model saved |
| 24 | Risk data prep: PhysioNet 2019, missing values, 6-hour sepsis label, trend features, NEWS2 baseline | 7B.2, 7B.3 | Clean features; NEWS2 AUROC |

### Week 5: ML research and integration

| Day | Work | Features | Done when |
|---|---|---|---|
| 25 | Train LR, RF, XGBoost; class imbalance; metrics | 7B.1, 7B.4 | Results table vs. NEWS2 |
| 26 | SHAP; train on A / test on B and reverse | 7B.5, 7B.6 | Table showing the unseen-hospital drop |
| 27 | Fine-tune with 5/10/20% of new-hospital data; federated averaging | 7B.7 | **Main results table** saved |
| 28 | Isolation Forest vs. thresholds on fault log; AI4I 2020 | 7C.1–7C.4 | Precision/recall table; model saved |
| 29 | `predictions` app: load models at startup; hourly forecast; risk on each vital reading; store predictions | 7A.4, 7B.8 | Predictions appear while simulator runs |
| 30 | ML alerts; forecast chart; risk + SHAP in panel; risk history + NEWS2 on patient page | 6.2, 8.6, 8.4 (part 2), 8.11 (part 2) | **Checkpoint 3: ML is live.** Red bed explains why |

### Week 6: What-if, analytics, quality

| Day | Work | Features | Done when |
|---|---|---|---|
| 31 | Snapshot to plain Python objects; SimPy model reusing simulator distributions | 9.1, 9.2 | Baseline runs 72 h forward |
| 32 | Scenario types; 50 seeded runs averaged; `POST /api/whatif/` (Admin) | 9.3, 9.4 | API returns both curves; live data unchanged |
| 33 | What-if builder and results; saved scenarios; simulator control screen | 9.5, 9.6, 4.8 (screen) | Scenario run and compared from the browser |
| 34 | Trends; model performance; staff and threshold screens; audit log screen | 10.1, 10.2, 8.12, 8.19 | All pages work with real data |
| 35 | Remaining tests; Docker Compose; responsive layout; CSV export | 11.2, 11.4, 8.9, 10.3 | `docker compose up` works; all tests pass |
| 36 | User evaluation: 5–6 tasks, SUS questionnaire, 3–5 people | 11.5 | Results from at least 3 people |

### Week 7: Demo and report

| Day | Work | Done when |
|---|---|---|
| 37 | Fix top issues; rehearse demo (login → map → alert → explanation → forecast → what-if → results); record backup video | **Checkpoint 4: 10-minute demo runs without errors** |
| 38 | Report: Introduction, Problem, Objectives, Literature review (12–15 papers) | Chapters drafted |
| 39 | Report: System design (architecture, ER, data flow, use-case, sequence diagrams) | Diagrams done |
| 40 | Report: Implementation (one section per module; simulator calibration) | Chapter drafted |
| 41 | Report: Results (ML tables, unseen-hospital results, SUS), limitations, conclusion, future work | Chapter drafted |
| 42 | Abstract, references, formatting, table of contents, proofreading; 15–20 presentation slides | Submitted |

---

## 4. Checkpoints

| Checkpoint | Day | If more than 2 days behind |
|---|---|---|
| 1. Simulator complete | 11 | Drop 1.5 (audit log) and 6.7 (thresholds) |
| 2. Live frontend | 22 | Also drop 8.9 (responsive), 10.3 (CSV), 8.19 (audit log screen) |
| 3. ML live | 30 | Also drop 7A.5 (uncertainty band) and 9.6 (saved scenarios) |
| 4. Demo ready | 37 | Use a report day for fixes |

## 5. Data

- **PhysioNet 2019 Sepsis Challenge** (open access): risk model and unseen-hospital experiment (hospital systems A and B).
- **eICU demo** (open access): simulator calibration.
- **eICU full** (credentialed access, request early): bonus experiment if approved in time.
- **AI4I 2020** (open access): equipment anomaly experiments.
