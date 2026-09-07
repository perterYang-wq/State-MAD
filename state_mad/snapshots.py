from .schema import Snapshot

def make_pre_exposure_snapshot(s):
    return Snapshot(s.pre_exposure_snapshot_id,s.scenario_id,"parent",None,s.events[:3],(),(),s.version_new_id,s.decision_phase_id)
def fork_snapshot(parent, branch_id, additions=()):
    additions=tuple(additions)
    return Snapshot(parent.snapshot_id+":"+branch_id,parent.scenario_id,branch_id,parent.snapshot_hash,parent.event_ids,parent.message_ids+additions,parent.visible_message_ids+additions,parent.current_version_id,parent.phase_id)
