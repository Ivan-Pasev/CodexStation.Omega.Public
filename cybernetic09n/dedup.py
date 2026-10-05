"""Scoped publication object identity, dedup and supersession audit for Omega v0.9n."""
from __future__ import annotations
import copy, glob, hashlib, json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
SCOPE=json.loads((ROOT/"cybernetic09n/DEDUP_SCOPE.json").read_text())
SUPER=json.loads((ROOT/"cybernetic09n/SUPERSESSION_REGISTRY.json").read_text())

def canonical(v:Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def digest(v:Any)->str:
    return hashlib.sha256(canonical(v)).hexdigest()

def _norm_payload(item:dict[str,Any], id_field:str)->dict[str,Any]:
    x=copy.deepcopy(item)
    x.pop(id_field,None)
    # Status/version fields remain intentionally part of semantic payload.
    return x

def declarations()->list[dict[str,Any]]:
    out=[]
    for spec in SCOPE["declarations"]:
        doc=json.loads((ROOT/spec["path"]).read_text())
        for idx,item in enumerate(doc.get(spec["array"],[])):
            cid=item.get(spec["id_field"])
            out.append({
              "class":spec["class"],
              "path":spec["path"],
              "index":idx,
              "id_field":spec["id_field"],
              "canonical_id":cid,
              "payload_digest":digest(_norm_payload(item,spec["id_field"])),
              "item_digest":digest(item)
            })
    for p in sorted(glob.glob(str(ROOT/"publication/*.json"))):
        path=Path(p)
        doc=json.loads(path.read_text())
        cid=None
        id_field=None
        for key in SCOPE["publication_receipts"]["id_precedence"]:
            if doc.get(key):
                cid=str(doc[key]); id_field=key; break
        if cid:
            out.append({
              "class":SCOPE["publication_receipts"]["class"],
              "path":str(path.relative_to(ROOT)),
              "index":0,
              "id_field":id_field,
              "canonical_id":cid,
              "payload_digest":digest(_norm_payload(doc,id_field)),
              "item_digest":digest(doc)
            })
    return out

def _known_pairs():
    supers={(x["from"],x["to"]) for x in SUPER.get("supersessions",[])}
    aliases={frozenset((x["a"],x["b"])) for x in SUPER.get("aliases",[])}
    return supers,aliases

def audit(records:list[dict[str,Any]]|None=None)->dict[str,Any]:
    recs=records if records is not None else declarations()
    errors=[]
    by_id={}
    for r in recs:
        cid=r.get("canonical_id")
        if not cid:
            errors.append({"code":"MISSING_CANONICAL_ID","record":r})
            continue
        by_id.setdefault(cid,[]).append(r)
    duplicate_ids={k:v for k,v in by_id.items() if len(v)>1}
    for cid,items in duplicate_ids.items():
        errors.append({"code":"DUPLICATE_CANONICAL_ID","canonical_id":cid,"locations":[x["path"] for x in items]})

    supers,aliases=_known_pairs()
    by_payload={}
    for r in recs:
        by_payload.setdefault((r["class"],r["payload_digest"]),[]).append(r)
    payload_collisions=[]
    for (cls,pd),items in by_payload.items():
        ids=sorted({x["canonical_id"] for x in items})
        if len(ids)>1:
            unresolved=[]
            for i,a in enumerate(ids):
                for b in ids[i+1:]:
                    if (a,b) not in supers and (b,a) not in supers and frozenset((a,b)) not in aliases:
                        unresolved.append([a,b])
            if unresolved:
                payload_collisions.append({"class":cls,"payload_digest":pd,"ids":ids,"unresolved_pairs":unresolved})
                errors.append({"code":"IDENTICAL_PAYLOAD_DIFFERENT_IDS","class":cls,"ids":ids})

    known=set(by_id)
    for a,b in supers:
        if a not in known or b not in known:
            errors.append({"code":"SUPERSESSION_UNKNOWN_ID","from":a,"to":b})
    for pair in aliases:
        for x in pair:
            if x not in known:
                errors.append({"code":"ALIAS_UNKNOWN_ID","id":x})

    graph={}
    for a,b in supers: graph.setdefault(a,[]).append(b)
    visiting=set(); visited=set()
    def dfs(n):
        if n in visiting: return True
        if n in visited: return False
        visiting.add(n)
        for m in graph.get(n,[]):
            if dfs(m): return True
        visiting.remove(n); visited.add(n); return False
    if any(dfs(n) for n in list(graph)):
        errors.append({"code":"SUPERSESSION_CYCLE"})

    return {
      "status":"PASS" if not errors else "FAIL",
      "scope_id":SCOPE["scope_id"],
      "record_count":len(recs),
      "class_counts":{c:sum(1 for r in recs if r["class"]==c) for c in sorted({r["class"] for r in recs})},
      "duplicate_id_count":len(duplicate_ids),
      "payload_collision_count":len(payload_collisions),
      "supersession_count":len(supers),
      "alias_count":len(aliases),
      "errors":errors,
      "authority_delta":"NONE",
      "does_not_establish":SCOPE["excluded_from_pass"]
    }
