import asyncio
from datetime import datetime
from src.core.database import AsyncSessionLocal
from src.agents.appointment_agent import AppointmentAgent
from src.agents.emergency_agent import EmergencyAgent
from src.agents.inventory_agent import InventoryAgent
from src.agents.billing_agent import BillingAgent
from src.agents.patient_agent import PatientAgent

async def run_tests():
    async with AsyncSessionLocal() as session:
        print("\n--- 1. Testing Patient Intent Agent ---")
        p_agent = PatientAgent()
        intent = await p_agent.parse_intent("My father is having intense chest pains and difficulty breathing!")
        print("Intent Detected:", intent)

        print("\n--- 2. Testing Emergency Agent ---")
        e_agent = EmergencyAgent()
        res_emg = await e_agent.triage_and_admit(session, patient_id=1, symptoms="severe chest pain and collapse")
        print("Emergency Action:", res_emg.action_taken)
        print("Emergency Summary:", res_emg.summary_message)

        print("\n--- 3. Testing Inventory Agent ---")
        inv_agent = InventoryAgent()
        res_inv = await inv_agent.audit_stock_and_alert(session)
        print("Critical Items:", res_inv.details["critical_medicines"])
        print("Inventory Summary:", res_inv.summary_message)

        print("\n--- 4. Testing Appointment Agent ---")
        app_agent = AppointmentAgent()
        res_app = await app_agent.book_appointment(session, patient_id=1, specialty="Cardiology", preferred_time=datetime(2025, 5, 10, 10, 0))
        print("Appointment Action:", res_app.action_taken)
        print("Appointment Summary:", res_app.summary_message)

        print("\n--- 5. Testing Billing Agent ---")
        bill_agent = BillingAgent()
        res_bill = await bill_agent.generate_bill(session, patient_id=1, bed_days=2, bed_type="ICU", has_insurance=True)
        print("Billing Action:", res_bill.action_taken)
        print("Billing Summary:", res_bill.summary_message)

if __name__ == "__main__":
    asyncio.run(run_tests())