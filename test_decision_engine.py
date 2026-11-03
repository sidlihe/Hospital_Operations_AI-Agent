import asyncio
from src.core.database import AsyncSessionLocal
from src.orchestrator.workflow import hospital_graph

async def test_full_pipeline():
    async with AsyncSessionLocal() as session:
        # Case 1: Critical Emergency Simulation
        print("\n================ TEST 1: CRITICAL EMERGENCY ================")
        state_emergency = {
            "session": session,
            "patient_id": 101,
            "user_query": "EMERGENCY: Patient collapsed, unresponsive and stopped breathing!",
            "symptoms": "collapsed, unresponsive, stopped breathing",
            "vitals": "Pulse undetectable",
            "specialty": "Emergency Medicine",
            "intent": "",
            "decision_result": {},
            "agent_output": {},
            "final_response": ""
        }
        res_emg = await hospital_graph.ainvoke(state_emergency)
        print("Decision Reasoning:", res_emg["decision_result"]["reasoning"])
        print("Alerts:", res_emg["decision_result"]["alerts"])
        print("Final Output:\n", res_emg["final_response"])

        # Case 2: Routine Appointment Simulation
        print("\n================ TEST 2: ROUTINE APPOINTMENT ================")
        state_apt = {
            "session": session,
            "patient_id": 102,
            "user_query": "I would like to schedule a cardiology routine checkup with Dr. Sarah Smith.",
            "symptoms": "routine heart checkup",
            "vitals": "Normal",
            "specialty": "Cardiology",
            "intent": "",
            "decision_result": {},
            "agent_output": {},
            "final_response": ""
        }
        res_apt = await hospital_graph.ainvoke(state_apt)
        print("Decision Reasoning:", res_apt["decision_result"]["reasoning"])
        print("Final Output:\n", res_apt["final_response"])

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())