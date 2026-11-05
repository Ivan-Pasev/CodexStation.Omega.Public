#!/usr/bin/env bash
# Synthetic single-runner containment smoke; NOT the two-host UHP pilot.
# Only public fixed fixture. No model, provider token, registry pull or push.
set -euo pipefail
if [[ "$(printenv CI 2>/dev/null || true)" != "true" ]]; then
  echo "UHP07 requires an explicit CI disposable-runner context" >&2
  exit 3
fi
command -v docker >/dev/null
command -v go >/dev/null
command -v python >/dev/null
root="$(git rev-parse --show-toplevel)"
cd "$root"
tmp="$(mktemp -d)"
image="codexstation-uhp07-synthetic:local"
cid=""
cleanup() {
  if [[ -n "$cid" ]]; then docker rm -f "$cid" >/dev/null 2>&1 || true; fi
  docker rmi "$image" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT
mkdir -p "$tmp/source" "$root/build/uhp07"
chmod 755 "$tmp" "$tmp/source"
printf 'CODEXSTATION_UHP07_PUBLIC_SYNTHETIC_FIXTURE\n' > "$tmp/source/fixture.txt"
chmod 644 "$tmp/source/fixture.txt"
before="$(sha256sum "$tmp/source/fixture.txt" | cut -d ' ' -f1)"
# Compile from the pinned checkout. No Go dependencies or external fetch.
CGO_ENABLED=0 GO111MODULE=off go build -trimpath -o "$tmp/worker" "./ops/uhp07/worker_probe.go"
cat > "$tmp/Dockerfile" <<'DOCKERFILE'
FROM scratch
COPY worker /worker
USER 65534:65534
ENTRYPOINT ["/worker"]
DOCKERFILE
# FROM scratch never pulls a registry image; network disabled during build.
docker build --no-cache --pull=false --network=none -t "$image" "$tmp" >/dev/null
cid="$(docker create \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 32 \
  --memory 134217728 \
  --cpus 0.5 \
  --user 65534:65534 \
  --mount "type=bind,src=$tmp/source,dst=/source,readonly" \
  "$image")"
docker start "$cid" >/dev/null
worker_exit="$(docker wait "$cid")"
docker logs "$cid"
docker inspect "$cid" > "$tmp/inspect.json"
after="$(sha256sum "$tmp/source/fixture.txt" | cut -d ' ' -f1)"
python - "$tmp/inspect.json" "$worker_exit" "$before" "$after" "$root/build/uhp07/receipt.json" <<'PY'
import json
import sys
from pathlib import Path
from runtime08c.uhp_ci_containment import assess_ci_containment
path, code, before, after, destination = sys.argv[1:]
inspections = json.loads(Path(path).read_text(encoding="utf-8"))
if not isinstance(inspections, list) or len(inspections) != 1:
    raise SystemExit("Expected exactly one Docker inspect object")
receipt = assess_ci_containment(inspections[0], int(code), before, after)
Path(destination).write_text(
    json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
)
print("UHP07:", receipt["verdict"], "source_unchanged:", receipt["source_snapshot_unchanged"])
if receipt["reasons"]:
    print("HOLD reasons:", ", ".join(receipt["reasons"]))
if receipt["verdict"] != "SINGLE_RUNNER_SMOKE_SHAPE_ONLY":
    raise SystemExit(1)
PY
if [[ -n "$(printenv GITHUB_STEP_SUMMARY 2>/dev/null || true)" ]]; then
  {
    echo "### UHP07 synthetic containment smoke"
    echo "One ephemeral CI runner only; no second host or independent attestation."
    echo "No provider, agent, network, real secrets, or canonical promotion."
    echo 'Verdict: SINGLE_RUNNER_SMOKE_SHAPE_ONLY; external qualification: HOLD.'
  } >> "$GITHUB_STEP_SUMMARY"
fi
