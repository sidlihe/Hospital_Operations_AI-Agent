from src.models.db_models import PriorityLevel, BedType

class EmergencyService:
    """
    Standard Emergency Severity Index (ESI) Triage Classification
    """
    @staticmethod
    def classify_esi(symptoms: str, vitals: str = "Normal") -> dict:
        text = f"{symptoms.lower()} {vitals.lower()}"

        # Level 1: Immediate resuscitation
        if any(w in text for w in ["cardiac arrest", "unresponsive", "stopped breathing", "severe trauma", "anaphylaxis"]):
            return {
                "priority": PriorityLevel.LEVEL_1_CRITICAL,
                "recommended_bed": BedType.ICU,
                "recommended_specialty": "Emergency Medicine",
                "immediate_action": "Code Blue / Immediate Trauma Bay Activation"
            }

        # Level 2: High risk / Emergent
        if any(w in text for w in ["chest pain", "stroke", "severe dyspnea", "heavy bleeding", "altered mental status"]):
            return {
                "priority": PriorityLevel.LEVEL_2_EMERGENT,
                "recommended_bed": BedType.EMERGENCY,
                "recommended_specialty": "Emergency Medicine",
                "immediate_action": "Stat physician evaluation within 10 minutes"
            }

        # Level 3: Urgent
        if any(w in text for w in ["fracture", "moderate asthma", "abdominal pain", "high fever"]):
            return {
                "priority": PriorityLevel.LEVEL_3_URGENT,
                "recommended_bed": BedType.GENERAL,
                "recommended_specialty": "Orthopedics" if "fracture" in text else "General Medicine",
                "immediate_action": "Assign standard triage queue"
            }

        # Level 4/5: Non-urgent
        return {
            "priority": PriorityLevel.LEVEL_5_NON_URGENT,
            "recommended_bed": BedType.GENERAL,
            "recommended_specialty": "General Medicine",
            "immediate_action": "Outpatient clinic or routine consultation"
        }