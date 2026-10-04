# CodexStation Ω Public — Deployment Candidates v0.6

Status: DEPLOYMENT_CANDIDATE / NOT RELEASED

Semantic parent fingerprint:

`eb43face6ab49b0eab112b5c9ddc6308a5dc0444c3d140622365c61976138719`

Cross-provider parity fingerprint:

`7ebb3332e2596fc53a2f956bbe26bf558fa96a93c159d0190625d10993d3dcd1`

## ChatGPT plugin candidate

Archive:

`codexstation-omega-public.zip`

SHA-256:

`f5bca8051c8d760e69a55dd55c4b9af98807113b3e14123b1253eba09d040714`

The archive root contains `plugin.json`, `.codex-plugin/plugin.json`, `AGENTS.md`, a single public Ω orchestrator skill, and dense public reference carriers.

Upload the ZIP as a plugin candidate. After installation, do not mark runtime conformance PASS until a distinct clean-chat regression exercises bundled fallback and identity/authority invariants.

## Gemini Notebook candidate

Archive:

`codexstation-omega-public-gemini-notebook.zip`

SHA-256:

`60d90cd81e2d9186aaeae89268137d99e48adcb935af9e7434e5e6c05bf1c2c4`

Unpack the transport ZIP. Attach the recommended Markdown sources beginning with `START_HERE.md`; the `_machine/` JSON layer is for exact registry/provenance inspection when needed.

Do not treat ZIP transport, source attachment, or Notebook summarization as authority promotion.

## Live gates

```text
CHATGPT_PLUGIN_PACKAGING = PASS_CANDIDATE
GEMINI_NOTEBOOK_PACKAGING = PASS_CANDIDATE

RGT-04_BUNDLED_FALLBACK_CLEAN_CHAT = OPEN
NB00_LIVE_CONFORMANCE_01 = OPEN

LICENSE_IP_REVIEW = OPEN
RELEASE_ELIGIBLE = false
AUTHORITY_DELTA = NONE
```

Packaging evidence is not live runtime evidence.
