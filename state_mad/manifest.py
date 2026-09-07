import platform, subprocess, sys
from .schema import digest

def build_manifest(config, artifacts, preflight, command, started_at, repo_probe=None, effective=None):
    if not preflight.get("passed"): raise ValueError("passed preflight required")
    if repo_probe is None:
        def git(*a): return subprocess.check_output(("git",)+a,text=True).strip()
        repo_probe={"sha":git("rev-parse","HEAD"),"branch":git("branch","--show-current"),"dirty":bool(git("status","--porcelain"))}
    return {"schema":"state-mad-manifest-v1","repository":repo_probe,"config_hash":digest(config),"artifact_hashes":dict(artifacts),"preflight":preflight,"effective_generation":dict(effective or {}),"command":tuple(command),"started_at":started_at,"python":sys.version,"platform":platform.platform()}
def finalize_manifest(manifest,ended_at,usage,cache_stats):
    required=("scenario","validation","prompts","calls","lineage")
    missing=[x for x in required if x not in manifest["artifact_hashes"]]
    if missing: raise ValueError("missing artifacts: "+",".join(missing))
    return {**manifest,"ended_at":ended_at,"usage":usage,"cache_stats":cache_stats,"manifest_hash":digest(manifest)}
