5 Autonomous Agents: Appointment, Billing, Inventory, Emergency, Patient.
4 Capabilities: Doctor Scheduling, Bed Management, Shortage Prediction, Emergency Prioritization.
Decision Engine: Dynamic LangGraph evaluation based on Resource Availability, Patient Priority, and Physician Rosters.

## Hospital operations console

The admin console reads bed capacity, the full physician roster, and medicine forecasts from the FastAPI service. Administrators can set a doctor's on-duty status and record medicine receipts or usage; each inventory movement records a reason and is rejected if it would make stock negative. API failures are surfaced in the console instead of being silently replaced with empty data.

Returning-patient registry matching requires a matching mobile number and email plus a partial name match. New patient details are registered when no matching contact information exists. This registry check is not SMS/OTP identity proof and does not replace staff verification.

The frontend defaults to `http://localhost:8000/api/v1`. Set `VITE_API_BASE_URL` when the API is hosted elsewhere. Start the API with `uvicorn src.main:app --reload` and the frontend from `frontend` with `npm run dev`.

## Recreate and seed the database

Stop the API before removing the SQLite database file. The default database path is `data/hospital.db` (configured by `DATABASE_URL` in `.env`); `hospital.db` is the filename, not `hospital_data.db`. From the repository root, run `python seed.py`. The script creates the database and current tables if they do not exist, then inserts the sample doctors, beds, medicines, and patient. It is safe to run again: existing seed records are left unchanged.