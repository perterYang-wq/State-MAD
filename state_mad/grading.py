import re
from dataclasses import dataclass

CLASSES=("CURRENT","STALE","STATIC_WRONG","OTHER/INVALID")
@dataclass(frozen=True)
class Grade:
    parsed_output: str|None; answer_class: str; status: str; reason: str|None
def grade_output(raw_output, answer_pool):
    text=raw_output.decode() if isinstance(raw_output,bytes) else raw_output
    matches=re.findall(r"(?m)^ANSWER=([^\r\n]+)$",text)
    if len(matches)!=1: return Grade(None,"OTHER/INVALID","invalid","ANSWER_FIELD_COUNT")
    value=matches[0]; mapping={answer_pool.current:"CURRENT",answer_pool.stale:"STALE",answer_pool.static_wrong:"STATIC_WRONG"}
    if value not in mapping: return Grade(value,"OTHER/INVALID","invalid","UNKNOWN_OR_NONCANONICAL")
    if sum(v in text for v in mapping if v!=value): return Grade(value,"OTHER/INVALID","invalid","EXTRA_CANDIDATE")
    return Grade(value,mapping[value],"valid",None)
