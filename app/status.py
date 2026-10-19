from enum import Enum
class Status(str,Enum):
    RECEIVED="RECEIVED"; VALIDATING="VALIDATING"; VALIDATION_FAILED="VALIDATION_FAILED"
    READY_TO_SUBMIT="READY_TO_SUBMIT"; SUBMISSION_IN_PROGRESS="SUBMISSION_IN_PROGRESS"
    SUBMISSION_UNKNOWN="SUBMISSION_UNKNOWN"; ASP_ACCEPTED="ASP_ACCEPTED"
    DELIVERED="DELIVERED_TO_BUYER_ASP"; REPORTED="REPORTED_TO_FTA"
    REJECTED="REJECTED"; FAILED="SUBMISSION_FAILED"; MANUAL_REVIEW="MANUAL_REVIEW"
MAP_A={"RECEIVED":Status.ASP_ACCEPTED,"VALIDATED":Status.ASP_ACCEPTED,"DELIVERED":Status.DELIVERED,"REPORTED":Status.REPORTED,"REJECTED":Status.REJECTED}
MAP_B={"QUEUED":Status.ASP_ACCEPTED,"ACCEPTED":Status.ASP_ACCEPTED,"BUYER_RECEIVED":Status.DELIVERED,"TAX_CONFIRMED":Status.REPORTED,"FAILED":Status.FAILED}
RANK={Status.RECEIVED:0,Status.VALIDATING:1,Status.READY_TO_SUBMIT:2,Status.SUBMISSION_IN_PROGRESS:3,Status.SUBMISSION_UNKNOWN:3,Status.ASP_ACCEPTED:4,Status.DELIVERED:5,Status.REPORTED:6}
def normalize(asp,status):
    m=MAP_A if asp=="asp_a" else MAP_B
    if status not in m: raise ValueError(f"Unsupported status {status!r} for {asp}")
    return m[status]
def can_advance(current,incoming):
    try: current=Status(current)
    except ValueError: return True
    if incoming in (Status.REJECTED,Status.FAILED): return True
    return RANK.get(incoming,-1)>=RANK.get(current,-1)
