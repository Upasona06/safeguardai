"""
LegalMapper — maps detected harm categories and risk levels
to applicable Indian laws (IT Act 2000, IPC, POCSO, etc.)
"""

from typing import List
from backend.models.schemas import LegalMapping, RiskLevel


                                                                    
LEGAL_DB = {
    "threat": [
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 503 — Criminal Intimidation",
            description=(
                "Whoever threatens another with injury to their person, reputation, or property, "
                "with intent to cause alarm, is guilty of criminal intimidation."
            ),
            severity="HIGH",
        ),
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 506 — Punishment for Criminal Intimidation",
            description=(
                "Punishment for criminal intimidation: imprisonment up to 2 years or fine, "
                "or both. If the threat is to cause death or grievous hurt: up to 7 years."
            ),
            severity="HIGH",
        ),
        LegalMapping(
            law="Information Technology Act",
            section="IT Act Section 66A — Online Threats (Reference)",
            description=(
                "While Section 66A was struck down, online threats remain punishable under "
                "IPC 503/506 and the IT Act's intermediary liability provisions."
            ),
            severity="MEDIUM",
        ),
    ],
    "cyberbullying": [
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 499/500 — Defamation",
            description=(
                "Making or publishing false statements intending to harm reputation. "
                "Includes online platforms. Punishable with up to 2 years imprisonment."
            ),
            severity="MEDIUM",
        ),
        LegalMapping(
            law="Information Technology Act",
            section="IT Act Section 66C/66D — Identity Theft & Cheating",
            description=(
                "Using someone's identity online fraudulently or for harassment. "
                "Punishable with up to 3 years and fine up to ₹1 lakh."
            ),
            severity="MEDIUM",
        ),
    ],
    "hate_speech": [
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 153A — Promoting Enmity",
            description=(
                "Promoting disharmony or feelings of enmity, hatred, or ill-will between "
                "different groups on grounds of religion, race, place of birth, etc. "
                "Punishable with up to 3 years imprisonment."
            ),
            severity="HIGH",
        ),
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 295A — Deliberate Acts to Outrage Religious Feelings",
            description=(
                "Deliberate and malicious acts intended to outrage religious feelings. "
                "Punishable with up to 3 years, or fine, or both."
            ),
            severity="HIGH",
        ),
    ],
    "sexual_harassment": [
        LegalMapping(
            law="Indian Penal Code",
            section="IPC Section 354A — Sexual Harassment",
            description=(
                "Making sexually coloured remarks, showing pornography against will, "
                "or demanding sexual favours. Punishable with up to 3 years."
            ),
            severity="HIGH",
        ),
        LegalMapping(
            law="Information Technology Act",
            section="IT Act Section 67 — Publishing Obscene Material",
            description=(
                "Publishing or transmitting obscene material in electronic form. "
                "First conviction: up to 3 years. Subsequent: up to 5 years."
            ),
            severity="HIGH",
        ),
    ],
    "grooming": [
        LegalMapping(
            law="Protection of Children from Sexual Offences Act",
            section="POCSO Section 11 — Sexual Harassment of Child",
            description=(
                "Any communication made with sexual intent to a child, including through "
                "electronic means. Punishable with up to 3 years and fine."
            ),
            severity="CRITICAL",
        ),
        LegalMapping(
            law="Protection of Children from Sexual Offences Act",
            section="POCSO Section 13 — Using Child for Pornographic Purposes",
            description=(
                "Using a child for pornographic purposes, including inducing a child to "
                "exhibit the sexual organs. Punishable with up to 5 years."
            ),
            severity="CRITICAL",
        ),
        LegalMapping(
            law="Information Technology Act",
            section="IT Act Section 67B — Child Pornography",
            description=(
                "Publishing, transmitting, or browsing content depicting children in "
                "sexually explicit acts. First conviction: up to 5 years and ₹10 lakh fine."
            ),
            severity="CRITICAL",
        ),
    ],
}

                                                        
SCORE_THRESHOLD = 0.25


class LegalMapper:
    def map(self, scores: dict, risk_level: str) -> List[LegalMapping]:
        mappings: List[LegalMapping] = []
        seen_sections: set = set()

        for category, laws in LEGAL_DB.items():
            score = scores.get(category, 0.0)
            if score < SCORE_THRESHOLD:
                continue
                                                                                     
            for law in laws:
                if law.section not in seen_sections:
                    if risk_level in ("CRITICAL", "HIGH") or law.severity in ("HIGH", "CRITICAL"):
                        mappings.append(law)
                        seen_sections.add(law.section)

                                       
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        mappings.sort(key=lambda x: severity_order.get(x.severity, 99))
        return mappings[:6]                             
