# app/utils/state_machine.py

VALID_TRANSITIONS = {
    "INITIATED": ["FUNDED"],
    "FUNDED": ["WORK_SUBMITTED", "REFUNDED"],
    "WORK_SUBMITTED": ["APPROVED_FOR_RELEASE", "DISPUTED"],
    "APPROVED_FOR_RELEASE": ["RELEASED", "DISPUTED", "REFUNDED"],
    "DISPUTED": ["RELEASED", "REFUNDED"],
}

def can_transition(current, new):
    return new in VALID_TRANSITIONS.get(current, [])
