from __future__ import annotations
import json, os
from pathlib import Path
from .schema import EffectiveGenerationIdentity, canonical_bytes, digest

class CacheIntegrityError(RuntimeError): pass
def build_cache_key(identity: EffectiveGenerationIdentity): return digest(identity)

class MessageCache:
    def __init__(self, root): self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def _path(self,key): return self.root/(key.replace(":","_")+".json")
    def lookup(self,key):
        p=self._path(key)
        if not p.exists(): return ("MISS",None)
        try:
            data=json.loads(p.read_text()); payload=data["payload"]
            if data["checksum"]!=digest(payload) or payload["cache_key"]!=key: raise ValueError("checksum/key mismatch")
            return ("HIT",payload)
        except Exception as e: raise CacheIntegrityError(f"invalid cache entry {key}: {e}") from e
    def commit_miss(self,key,payload):
        p=self._path(key)
        if p.exists(): raise CacheIntegrityError("refusing duplicate cache commit")
        body={"schema":"state-mad-cache-v1","payload":payload,"checksum":digest(payload)}
        tmp=p.with_suffix(".tmp")
        with open(tmp,"x",encoding="utf-8") as f:
            f.write(canonical_bytes(body).decode()); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,p)
