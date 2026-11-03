from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.logger import logger
from src.models.schemas import ESIClassification
from src.models.db_models import PriorityLevel, BedType

CLINICAL_TRIAGE_SYSTEM_PROMPT = """
You are an expert Chief Medical Triage Officer at a major level-1 trauma hospital.
You evaluate raw, unpredictable patient requests using the official **Emergency Severity Index (ESI v4)** algorithm.

### CLINICAL DECISION MATRIX:
- **ESI 1 (LEVEL_1_CRITICAL)**:
  * Patient requires immediate life-saving intervention.
  * Phrasing signals: "unresponsive", "blue lips", "gasping", "collapsed", "massive bleeding", "no pulse", "overdose with apnea", "severe anaphylaxis".
  * Assign: BedType.ICU, PriorityLevel.LEVEL_1_CRITICAL.

- **ESI 2 (LEVEL_2_EMERGENT)**:
  * High-risk situation, severe pain (>=7/10), acute altered mental status, or sudden critical symptoms.
  * Phrasing signals: Any acute chest pain, tightness or pressure, pain radiating to left arm/jaw, stroke signs (FAST: facial droop, arm weakness, slurred speech), testicular torsion, sudden severe headache ("worst headache of life"), acute asthma not responding to inhaler, severe suicidal ideation.
  * Assign: BedType.EMERGENCY, PriorityLevel.LEVEL_2_EMERGENT.

- **ESI 3 (LEVEL_3_URGENT)**:
  * Vitals currently stable, but requires **2 or more diagnostic/therapeutic resources** (e.g., Blood labs + CT scan, IV antibiotics + X-ray).
  * Phrasing signals: Moderate abdominal pain, fractured limb with intact pulse, persistent high fever, moderate laceration, kidney stones.
  * Assign: BedType.GENERAL, PriorityLevel.LEVEL_3_URGENT.

- **ESI 4 (LEVEL_4_SEMI_URGENT)**:
  * Stable. Requires **1 resource** (e.g., Simple X-ray only, simple suture, oral meds).
  * Assign: BedType.GENERAL, PriorityLevel.LEVEL_4_SEMI_URGENT.

- **ESI 5 (LEVEL_5_NON_URGENT)**:
  * Stable. Requires **0 resources** (e.g., Suture removal, medication refills, routine chronic consult, mild rash without fever, doctor note).
  * Assign: BedType.GENERAL, PriorityLevel.LEVEL_5_NON_URGENT.

Extract clinical meaning regardless of slang, typos, panic, or casual patient language.
"""

class EmergencyService:
    @staticmethod
    async def classify_esi(symptoms: str, vitals: str = "Normal") -> ESIClassification:
        logger.info(f"[EmergencyService] Evaluating raw inputs -> symptoms='{symptoms}' | vitals='{vitals}'")

        llm = get_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(ESIClassification)

        prompt = ChatPromptTemplate.from_messages([
            ("system", CLINICAL_TRIAGE_SYSTEM_PROMPT),
            ("human", "PATIENT COMPLAINT / RAW INPUT:\n{symptoms}\n\nREPORTED VITALS / CONTEXT:\n{vitals}")
        ])

        chain = prompt | structured_llm

        try:
            result: ESIClassification = await chain.ainvoke({
                "symptoms": symptoms,
                "vitals": vitals
            })
            logger.info(
                f"[EmergencyService] Triage Decision: ESI Level={result.esi_level} | "
                f"Priority={result.priority.value} | Bed={result.recommended_bed.value} | "
                f"Specialty={result.recommended_specialty}"
            )
            return result
        except Exception as e:
            logger.error(f"[EmergencyService] Structured triage extraction error: {e}", exc_info=True)
            # Safe clinical fallback: default to high-alert if parsing fails on unknown input
            return ESIClassification(
                raw_symptom_analysis="Parsing exception occurred. Failsafe activated.",
                esi_level=2,
                priority=PriorityLevel.LEVEL_2_EMERGENT,
                recommended_bed=BedType.EMERGENCY,
                recommended_specialty="Emergency Medicine",
                life_threat_detected=True,
                clinical_justification="Automated triage fallback to prevent under-triage of potentially unstable patient.",
                immediate_orders=["Immediate Bedside Clinical Evaluation", "Vital Signs Check"]
            )