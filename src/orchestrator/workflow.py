from typing import TypedDict, Any, Dict
from datetime import datetime
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.patient_agent import PatientAgent
from src.agents.emergency_agent import EmergencyAgent
from src.agents.appointment_agent import AppointmentAgent
from src.agents.billing_agent import BillingAgent
from src.agents.inventory_agent import InventoryAgent
from src.orchestrator.decision_engine import DecisionEngine
from src.core.logger import logger


class HospitalWorkflowState(TypedDict):
    session: AsyncSession
    patient_id: int
    user_query: str
    symptoms: str
    vitals: str
    specialty: str
    intent: str
    decision_result: Dict[str, Any]
    agent_output: Dict[str, Any]
    final_response: str


# Node 1: Intelligent Intake Node
async def intake_node(state: HospitalWorkflowState) -> dict:
    patient_agent = PatientAgent()
    analysis = await patient_agent.parse_intent(state["user_query"])
    
    # If the intake detects extracted symptoms, enrich the symptoms state
    symptoms = state.get("symptoms") or analysis.extracted_symptoms or state["user_query"]
    
    return {
        "intent": analysis.detected_intent,
        "symptoms": symptoms
    }


# Node 2: Multi-Factor Decision Node
async def decision_node(state: HospitalWorkflowState) -> dict:
    decision = await DecisionEngine.evaluate_admission_or_intake(
        session=state["session"],
        symptoms=state["symptoms"],
        vitals=state.get("vitals", "Normal")
    )
    return {"decision_result": decision.model_dump()}


# Node 3: Emergency Agent Node
async def emergency_node(state: HospitalWorkflowState) -> dict:
    agent = EmergencyAgent()
    res = await agent.triage_and_admit(
        session=state["session"],
        patient_id=state["patient_id"],
        symptoms=state["symptoms"],
        vitals=state.get("vitals", "Normal")
    )
    return {
        "agent_output": res.model_dump(),
        "final_response": res.summary_message
    }


# Node 4: Appointment Agent Node
async def appointment_node(state: HospitalWorkflowState) -> dict:
    agent = AppointmentAgent()
    res = await agent.book_appointment(
        session=state["session"],
        patient_id=state["patient_id"],
        specialty=state.get("specialty", "General Medicine"),
        preferred_time=datetime.utcnow()
    )
    return {
        "agent_output": res.model_dump(),
        "final_response": res.summary_message
    }


# Node 5: Billing Agent Node
async def billing_node(state: HospitalWorkflowState) -> dict:
    agent = BillingAgent()
    res = await agent.generate_bill(
        session=state["session"],
        patient_id=state["patient_id"],
        bed_days=1,
        bed_type="GENERAL"
    )
    return {
        "agent_output": res.model_dump(),
        "final_response": res.summary_message
    }


# Node 6: Inventory Agent Node
async def inventory_node(state: HospitalWorkflowState) -> dict:
    agent = InventoryAgent()
    res = await agent.audit_stock_and_alert(session=state["session"])
    return {
        "agent_output": res.model_dump(),
        "final_response": res.summary_message
    }


def route_by_intent(state: HospitalWorkflowState) -> str:
    target = state.get("intent", "APPOINTMENT").upper()
    if target == "EMERGENCY":
        return "emergency"
    elif target == "BILLING":
        return "billing"
    elif target == "INVENTORY":
        return "inventory"
    return "appointment"


def build_hospital_orchestrator():
    builder = StateGraph(HospitalWorkflowState)

    builder.add_node("intake", intake_node)
    builder.add_node("decision_evaluator", decision_node)
    builder.add_node("emergency", emergency_node)
    builder.add_node("appointment", appointment_node)
    builder.add_node("billing", billing_node)
    builder.add_node("inventory", inventory_node)

    builder.set_entry_point("intake")
    builder.add_edge("intake", "decision_evaluator")

    builder.add_conditional_edges(
        "decision_evaluator",
        route_by_intent,
        {
            "emergency": "emergency",
            "appointment": "appointment",
            "billing": "billing",
            "inventory": "inventory"
        }
    )

    builder.add_edge("emergency", END)
    builder.add_edge("appointment", END)
    builder.add_edge("billing", END)
    builder.add_edge("inventory", END)

    return builder.compile()


hospital_graph = build_hospital_orchestrator()