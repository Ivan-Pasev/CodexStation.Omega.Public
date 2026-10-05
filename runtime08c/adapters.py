"""Source-family adapters for the CodexStation Ω v0.8c reference runtime.

Adapters are intentionally lossy where source types differ. They expose the loss
rather than asserting semantic identity.
"""

from __future__ import annotations

from typing import Any

from .runtime import digest, make_state


def adapt_digital_fabrica_transition(
    proposal: dict[str, Any],
    *,
    project_id: str,
    source_profile: str = "DIGITAL_FABRICA_CORE",
) -> dict[str, Any]:
    """Map a Digital.Fabrica.Core-like TransitionProposal to CandidateTransition."""
    return {
        "transition_id": proposal["transition_id"],
        "project_id": project_id,
        "parent_state_digest": proposal["parent_state_digest"],
        "proposer_principal_id": proposal["actor_id"],
        "kind": proposal.get("kind", "OPERATIONAL"),
        "operations": proposal.get("operations", []),
        "required_authority": proposal.get("required_authority", []),
        "protected_invariants": proposal.get("protected_invariants", []),
        "verification_plan": proposal.get("verification_plan", []),
        "reversibility": proposal.get("reversibility", "REVERSIBLE"),
        "evidence_refs": proposal.get("evidence_refs", []),
        "source_profile": source_profile,
        "adapter_loss": [
            "source-specific schema/policy fields not represented unless explicitly provided",
        ],
    }


def adapt_dfpl_gateway_request(
    request: dict[str, Any],
    authorization: dict[str, Any],
    *,
    project_id: str,
) -> dict[str, Any]:
    """Map a DFPL/PRIMA gateway request + authorization to CandidateTransition."""
    operations = request.get("operations", [])
    transition = {
        "transition_id": request.get("request_id", request.get("plan_id", "dfpl:transition")),
        "project_id": project_id,
        "parent_state_digest": request["parent_state_digest"],
        "proposer_principal_id": authorization["principal_id"],
        "kind": request.get("kind", "OPERATIONAL"),
        "operations": operations,
        "required_authority": authorization.get("required_capabilities", []),
        "protected_invariants": request.get("protected_invariants", []),
        "verification_plan": request.get("verification_plan", []),
        "reversibility": request.get("reversibility", "REVERSIBLE"),
        "evidence_refs": request.get("evidence_refs", []),
        "source_profile": "DFPL_PRIMA",
        "authorized_plan_digest": authorization.get("plan_digest"),
        "adapter_loss": [
            "DFPL semantic DecisionCertificate remains separate from runtime authorization",
            "PRIMA capability constraints not expressible as simple rights remain external obligations",
        ],
    }
    if transition["authorized_plan_digest"] is None:
        transition["authorized_plan_digest"] = digest("authorized-plan", operations)
    return transition


def adapt_highestone_state(
    source: dict[str, Any],
    *,
    project_id: str,
) -> dict[str, Any]:
    """Map HighestOne State/Grant representation to CanonicalState."""
    grants = []
    for item in source.get("grants", []):
        grants.append(
            {
                "grant_id": item.get("grant_id", f"highest:{item['actor']}"),
                "principal_id": item["actor"],
                "level": f"A{item.get('level', 0)}",
                "rights": item.get("rights", []),
                "scope": item.get("scope", ["*"]),
            }
        )
    return make_state(
        project_id=project_id,
        state_id=f"{source.get('rootId', 0)}:{source.get('branchId', 0)}:{source.get('revision', 0)}",
        revision=int(source.get("revision", 0)),
        payload={
            "highest_root_id": source.get("rootId"),
            "highest_branch_id": source.get("branchId"),
        },
        grants=grants,
        provenance_refs=["adapter:highestone"],
    )


def adapt_gilc_effect_intent(
    intent: dict[str, Any],
    state: dict[str, Any],
    *,
    project_id: str,
) -> dict[str, Any]:
    """Map GILC.CodexStation EffectIntent to an external EFFECT transition."""
    required = intent.get("required_authority", "A2")
    return {
        "transition_id": intent.get("intent_id", "gilc:effect"),
        "project_id": project_id,
        "parent_state_digest": state["digest"],
        "proposer_principal_id": intent["principal_id"],
        "kind": "OPERATIONAL",
        "operations": [
            {
                "op": "EFFECT",
                "effect_type": intent.get("effect_type", "UNSPECIFIED"),
                "parameters": intent.get("parameters", {}),
            }
        ],
        "required_authority": [required],
        "protected_invariants": intent.get("protected_invariants", []),
        "verification_plan": intent.get("verification_plan", []),
        "reversibility": intent.get("reversibility", "UNKNOWN"),
        "evidence_refs": intent.get("evidence_refs", []),
        "source_profile": "GILC_CODEXSTATION",
        "adapter_loss": [
            "host/provider execution semantics remain outside the pure reference runtime",
        ],
    }


def adapt_neural_lattice_state(
    cell: dict[str, Any],
    *,
    project_id: str,
) -> dict[str, Any]:
    """Map an NL-1-like State Cell into CanonicalState."""
    payload = {
        "cell_status": cell.get("status"),
        "cell_state": cell.get("state"),
        "cell_evidence": cell.get("evidence", []),
        "cell_authority": cell.get("authority", {}),
        "cell_time": cell.get("time"),
        "cell_conflict_status": cell.get("conflictStatus"),
    }
    conflicts = []
    if cell.get("conflictStatus") not in (None, "NONE", "CLOSED"):
        conflicts.append(
            {
                "conflict_id": f"nl:{cell.get('id', 'unknown')}:conflict",
                "conflict_type": "SOURCE_CONFLICT",
                "participants": [cell.get("id", "unknown")],
                "status": cell.get("conflictStatus"),
                "evidence_refs": [],
            }
        )
    return make_state(
        project_id=project_id,
        state_id=cell.get("id", "nl:state"),
        revision=int(cell.get("version", 0)),
        payload=payload,
        grants=[],
        provenance_refs=list(cell.get("provenance", [])) or ["adapter:neural-lattice"],
        conflicts=conflicts,
    )


ADAPTERS = {
    "DIGITAL_FABRICA_CORE": adapt_digital_fabrica_transition,
    "DFPL_PRIMA": adapt_dfpl_gateway_request,
    "HIGHESTONE": adapt_highestone_state,
    "GILC_CODEXSTATION": adapt_gilc_effect_intent,
    "NEURAL_LATTICE": adapt_neural_lattice_state,
}
