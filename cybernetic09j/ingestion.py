"""Host-return ingestion and live conformance aggregation for Omega v0.9j."""
from __future__ import annotations
import copy,json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
from cybernetic09i.acquisition import make_request, ingest_return, aggregate, digest

def ingest_batch(ledger:dict[str,Any], returned_envelopes:list[dict[str,Any]])->dict[str,Any]:
    out=copy.deepcopy(ledger)
    audit=[]
    accepted=0
    held=0
    rejected=0
    for returned in returned_envelopes:
        host=(returned.get("host_witness") or {}).get("host_id")
        if host not in out.get("hosts",{}):
            audit.append({
              "host_id":host,"request_id":returned.get("request_id"),
              "returned_digest":digest(returned),"verdict":"REJECT_UNKNOWN_HOST",
              "reasons":["UNKNOWN_HOST"],"ledger_before":None,"ledger_after":None
            })
            rejected+=1
            continue
        before=copy.deepcopy(out["hosts"][host])
        req=make_request(host)
        candidate,verdict=ingest_return(out,req,returned)
        if verdict.get("status")=="INGESTED":
            out=candidate
            accepted+=1
            v="INGESTED"
            reasons=[]
        else:
            held+=1
            v=verdict.get("status","HOLD")
            reasons=verdict.get("reasons",[])
        after=copy.deepcopy(out["hosts"][host])
        audit.append({
          "host_id":host,"request_id":returned.get("request_id"),
          "returned_digest":digest(returned),"verdict":v,
          "reasons":reasons,"ledger_before":before,"ledger_after":after
        })
    return {
      "ledger":out,
      "audit":audit,
      "counts":{"accepted":accepted,"held":held,"rejected":rejected,"received":len(returned_envelopes)},
      "aggregate":aggregate(out),
      "authority_delta":"NONE"
    }

def ingest_inbox(ledger:dict[str,Any], inbox:dict[str,Any])->dict[str,Any]:
    returns=inbox.get("returns",[])
    result=ingest_batch(ledger,returns)
    if not returns:
        result["status"]="HOLD_NO_RETURNED_HOST_ENVELOPES"
    elif result["aggregate"]["status"]=="LIVE_MULTI_HOST_CONFORMANCE_PASS":
        result["status"]="LIVE_MULTI_HOST_CONFORMANCE_PASS"
    else:
        result["status"]="PARTIAL_OR_HELD_LIVE_CONFORMANCE"
    return result
