# 🚨 ResQHub — Emergency Reporting & Intelligent Dispatch Platform

> **Emergency Response & Disaster Management System**  
> Operations-grade emergency triage and dispatch designed with a distinct point of view: high-contrast dark operations room for dispatchers, and an urgent, thumb-friendly mobile interface for citizens in distress.

---

## 🎨 Design Rationale (≤150 words)

> **For the Reporter:** A panicked citizen on a phone in sunlight needs to report an emergency in under 30 seconds with one thumb. We prioritized a fast-path button, large 48px category tiles, auto-GPS, and placed camera capture at the end as an optional step.  
> **For the Dispatcher:** A control room operator under pressure scanning dozens of incidents cannot waste time decoding decorative charts. We designed a dark operations-room aesthetic with a dominant Critical Queue, live elapsed timers, a monospace status strip, and a 3px left severity bar instead of distracting badges.  
> **3 Key Design Decisions:**  
> 1. **Red reserved exclusively for Critical:** Prevents alert fatigue and ensures immediate peripheral-vision recognition.  
> 2. **One-line monospace status strip instead of generic cards:** Gives the operator instant situational awareness (`11 open · 3 critical · oldest 47m`).  
> 3. **Ranked horizontal category bars instead of donut charts:** Enables instant visual comparison of incident volume without squinting at radial segments.

---

## 🔑 Demo Responder Accounts (Seeded & Verified)

All accounts are seeded idempotently in the SQLite database (`emergency_r2.db`) and are ready for live demonstration:

| Role / Vehicle | Name | Login Username | Password | Base Station Location (Chennai Area) | Status |
|---|---|---|---|---|---|
| **Ambulance 01** | Karthik Rajan | `amb01` | `responder123` | Apollo Greams Road, Thousand Lights | Available |
| **Ambulance 02** | Praveen Kumar | `amb02` | `responder123` | RGGGH Central Hospital, Chennai | Available |
| **Ambulance 03** | Senthil Nathan | `amb03` | `responder123` | MIOT International, Manapakkam | Available |
| **Fire Engine 01** | Murugan Selvam | `fe01` | `responder123` | Kilpauk Fire Station, Chennai | Available |
| **Fire Engine 02** | Venkatesh Babu | `fe02` | `responder123` | Guindy Industrial Estate Fire Station | Available |
| **Admin Control** | Control Room Admin | `admin` | `admin123` | Command Center Headquarters | Active |

---

## 📱 Live Endpoints & Phone Access

Run the application:
```bash
cd r2_platform
python app.py
```
*(Or double-click `run_round2.bat`)*

- **Citizen Mobile SOS**: [http://localhost:5000/](http://localhost:5000/) *(or on your phone via Wi-Fi at `http://192.168.137.190:5000/`)*
- **Dispatcher Command Dashboard**: [http://localhost:5000/admin](http://localhost:5000/admin)
- **Responder Field App**: [http://localhost:5000/responder](http://localhost:5000/responder)

---

## 📋 Verification Checklist (All 8 Items Passed)

- [x] **1. Driver Status Buttons**: Enforces strict progression (`En Route` ➔ `Arrived` ➔ `Completed`), disables out-of-order buttons, displays success/error toasts, and synchronizes the admin dashboard live.
- [x] **2. Demo Responder Accounts**: 5 accounts (3 ambulances, 2 fire engines) seeded and tested for login.
- [x] **3. Honest Alert Notification**: Shows real count of matching available units alerted, or an honest queued message (`No units free right now...`).
- [x] **4. 1 Active Task per Driver**: Server-enforced (`HTTP 409 Conflict`), and UI disables `Accept` with `"Finish your current task first"`.
- [x] **5. Release on Completion**: Completing a task marks the driver `Available` and clears them to accept new claims.
- [x] **6. Clean Language Switcher**: English / தமிழ் toggle at the top with single-language rendering and persistent dictionary.
- [x] **7. Camera Moved to End**: Optional step 4 with "Skip" support and standard file picker fallback.
- [x] **8. Clean Styling**: Tagline removed from all titles; KPI cards clean without decorative icons.
