import os
from pathlib import Path
from .schema import canonical_bytes, digest

class RunStore:
    def __init__(self,root): self.root=Path(root); self.run_dir=None
    def create(self,run_id):
        p=self.root/run_id
        p.mkdir(parents=True,exist_ok=False); (p/"messages").mkdir(); self.run_dir=p; return self
    def _append(self,name,record):
        with open(self.run_dir/name,"ab") as f: f.write(canonical_bytes(record)+b"\n"); f.flush(); os.fsync(f.fileno())
    def append_call(self,r): self._append("calls.jsonl",r)
    def append_lineage(self,r): self._append("lineage.jsonl",r)
    def put_message(self,m):
        p=self.run_dir/"messages"/(m.content_hash.replace(":","_")+".json")
        data=canonical_bytes(m)
        if p.exists():
            if p.read_bytes()!=data: raise RuntimeError("message hash collision")
            return
        with open(p,"xb") as f: f.write(data); f.flush(); os.fsync(f.fileno())
    def write_once(self,name,value):
        p=self.run_dir/name
        with open(p,"xb") as f: f.write(canonical_bytes(value)); f.flush(); os.fsync(f.fileno())
        return digest(value)
    def finalize(self,report): return self.write_once("report.json",report)
