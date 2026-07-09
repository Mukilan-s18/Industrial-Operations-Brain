"""
Day 10: Hardcoded Fallback Responses
Guaranteed perfect JSON responses for the 5 demo queries.
If the live pipeline (ChromaDB/Gemini API) crashes during the demo,
toggle USE_FALLBACK=True in app.py to serve these instantly.
"""

FALLBACK_RESPONSES = {
    "what is the pressure limit for hv-204?": {
        "answer": (
            "Based on [sop_101.txt, Rev 4], the maximum allowable operating pressure "
            "for valve HV-204 is 120 PSI. Exceeding this limit may cause seal failure.\n\n"
            "**WARNING — Contradiction Detected:** [sop_101_b.txt, Rev 2] states the limit "
            "is 150 PSI. Please consult an engineer to confirm the correct specification."
        ),
        "sources": [
            {"doc": "sop_101.txt", "revision": 4, "section": "Valve Pressure Limits"},
            {"doc": "sop_101_b.txt", "revision": 2, "section": "Valve Limits"},
        ],
        "contradiction_detected": True,
    },
    "failures related to p-101 in last 2 years": {
        "answer": (
            "Based on [wo_998.txt, Rev 1], Pump P-101 experienced a casing seal leak "
            "on 2025-11-04. The root cause was loose housing bolts measured at 20 Nm "
            "(specification is 45 Nm per [sop_101.txt, Rev 4]). Technician John Doe "
            "re-torqued the bolts and replaced the primary O-ring seal.\n\n"
            "The Knowledge Graph also records a Vibration Trip event on 2024-06-15."
        ),
        "sources": [
            {"doc": "wo_998.txt", "revision": 1, "section": "Resolution"},
            {"doc": "sop_101.txt", "revision": 4, "section": "Torque Specifications"},
            {
                "doc": "Knowledge Graph",
                "revision": None,
                "section": "P-101 failure modes",
            },
        ],
        "contradiction_detected": False,
    },
    "what is the torque specification for p-101 housing bolts?": {
        "answer": (
            "**WARNING — Contradiction Detected:**\n"
            "- [sop_101.txt, Rev 4] specifies **45 Nm** for P-101 housing bolts.\n"
            "- [sop_101_b.txt, Rev 2] specifies **30 Nm** for the same bolts.\n\n"
            "These two SOPs contradict each other. Please escalate to a senior engineer "
            "to confirm the correct torque value before proceeding with maintenance."
        ),
        "sources": [
            {"doc": "sop_101.txt", "revision": 4, "section": "Torque Specifications"},
            {"doc": "sop_101_b.txt", "revision": 2, "section": "Torque Specifications"},
        ],
        "contradiction_detected": True,
    },
    "what osha standard covers lockout tagout?": {
        "answer": (
            "Based on [osha_1910_147.txt, Rev 1], OSHA Standard 1910.147 covers "
            "the control of hazardous energy (lockout/tagout). It requires employers "
            "to establish energy control procedures, employee training, and periodic "
            "inspections to prevent unexpected energization during servicing."
        ),
        "sources": [
            {"doc": "osha_1910_147.txt", "revision": 1, "section": "Full document"}
        ],
        "contradiction_detected": False,
    },
    "what ppe is required for pump maintenance?": {
        "answer": (
            "Based on [sop_101.txt, Rev 4], the following PPE is required for "
            "Pump P-101 maintenance:\n"
            "- Gloves\n"
            "- Safety glasses\n\n"
            "Ensure all power is disconnected before servicing per OSHA 1910.147 "
            "lockout/tagout requirements [osha_1910_147.txt, Rev 1]."
        ),
        "sources": [
            {"doc": "sop_101.txt", "revision": 4, "section": "Safety Warnings"},
            {"doc": "osha_1910_147.txt", "revision": 1, "section": "Full document"},
        ],
        "contradiction_detected": False,
    },
}


import typing


def get_fallback(query: str) -> typing.Optional[dict]:
    """Look up a fallback response for the given query. Returns None if no fallback exists."""
    return FALLBACK_RESPONSES.get(query.lower().strip())
