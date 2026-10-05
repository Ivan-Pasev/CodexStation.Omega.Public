#!/usr/bin/env python3
"""Portable exact-pin runner for an already-authorized local source checkout.

No source text or command output is written to the public receipt.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILES=json.loads((ROOT/"runner08h/FAMILY_PROFILES.json").read_text())
FAMILIES=PROFILES["families"]

def git(source:Path,*args:str)->str:
    p=subprocess.run(["git",*args],cwd=source,text=True,capture_output=True)
    if p.returncode!=0:
        raise RuntimeError("git command failed: "+" ".join(args))
    return p.stdout.strip()

def clean(source:Path)->bool:
    return git(source,"status","--porcelain","--untracked-files=normal")== ""

def identity(source:Path)->dict:
    return {
        "head":git(source,"rev-parse","HEAD"),
        "clean":clean(source)
    }

def execute_step(source:Path,step:dict)->dict:
    cwd=(source/step["cwd"]).resolve()
    if not str(cwd).startswith(str(source.resolve())):
        return {"command":step["command"],"status":"FAIL","exit_code":126,"duration_ms":0}
    started=time.monotonic()
    p=subprocess.run(["bash","-lc",step["command"]],cwd=cwd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    elapsed=int((time.monotonic()-started)*1000)
    return {
        "command":step["command"],
        "status":"PASS" if p.returncode==0 else "FAIL",
        "exit_code":p.returncode,
        "duration_ms":elapsed
    }

def plan(family:str,source:Path)->dict:
    profile=FAMILIES[family]
    state=identity(source)
    return {
        "family":family,
        "repository":profile["repository"],
        "expected_source_commit":profile["source_commit"],
        "observed_source_commit":state["head"],
        "source_clean":state["clean"],
        "scope":profile["scope"],
        "steps":profile["steps"]
    }

def run(family:str,source:Path,provider:str,run_id:str,runner_commit:str)->dict:
    profile=FAMILIES[family]
    before=identity(source)
    pre_errors=[]
    if before["head"]!=profile["source_commit"]:
        pre_errors.append("SOURCE_COMMIT_MISMATCH")
    if not before["clean"]:
        pre_errors.append("SOURCE_NOT_CLEAN_BEFORE_RUN")

    results=[]
    if not pre_errors:
        for step in profile["steps"]:
            result=execute_step(source,step)
            results.append(result)
            if result["status"]!="PASS":
                break

    after=identity(source)
    mutation=not after["clean"] or after["head"]!=before["head"]
    if mutation:
        pre_errors.append("SOURCE_TREE_CHANGED_DURING_RUN")

    required=[s["command"] for s in profile["steps"]]
    result_map={x["command"]:x["status"] for x in results}
    if pre_errors:
        overall="FAIL"
    elif all(result_map.get(c)=="PASS" for c in required):
        overall="PASS"
    elif any(result_map.get(c)=="FAIL" for c in required):
        overall="FAIL"
    else:
        overall="HOLD"

    receipt={
        "schema":"GILC/CODEXSTATION/OMEGA-PRIVATE-REPRODUCTION-RECEIPT/0.8f",
        "source_family":family,
        "repository":profile["repository"],
        "source_commit":profile["source_commit"],
        "runner_identity":{
            "provider":provider,
            "run_id":run_id,
            "runner_commit":runner_commit,
            "runner_pack_id":PROFILES["runner_pack_id"],
            "platform":platform.platform(),
            "python":platform.python_version()
        },
        "commands":required,
        "results":[{"command":c,"status":result_map.get(c,"SKIP")} for c in required],
        "overall_status":overall,
        "scope":profile["scope"],
        "sanitized":True,
        "private_source_disclosed":False,
        "source_tree_modified_for_test":mutation,
        "authority_delta":"NONE",
        "evidence_class":"DIRECT_RUNNER_EXECUTION",
        "execution_metadata":{
            "preflight_errors":pre_errors,
            "step_exit_codes":{x["command"]:x["exit_code"] for x in results},
            "step_duration_ms":{x["command"]:x["duration_ms"] for x in results}
        }
    }
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--family",required=True,choices=sorted(FAMILIES))
    ap.add_argument("--source-dir",required=True)
    ap.add_argument("--provider",default="AUTHORIZED_LOCAL_RUNNER")
    ap.add_argument("--run-id",default=os.environ.get("CI_RUN_ID","manual"))
    ap.add_argument("--runner-commit",default=os.environ.get("RUNNER_COMMIT","unknown"))
    ap.add_argument("--receipt-out")
    ap.add_argument("--plan",action="store_true")
    args=ap.parse_args()
    source=Path(args.source_dir).resolve()
    if not (source/".git").exists():
        raise SystemExit("source-dir must be a git checkout")
    if args.plan:
        print(json.dumps(plan(args.family,source),indent=2))
        return 0
    receipt=run(args.family,source,args.provider,args.run_id,args.runner_commit)
    data=json.dumps(receipt,indent=2)+"\n"
    if args.receipt_out:
        Path(args.receipt_out).write_text(data)
    else:
        sys.stdout.write(data)
    return 0 if receipt["overall_status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
