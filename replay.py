"""Inspect an authored compatibility matrix. No TLS handshakes are performed."""
import argparse
import json
from dataclasses import replace
from fixtures import APPROVED, NEW, NOW, baseline, edges, incident, safe_plan, rotate_first_plan
from model import apply_step, edge_errors
from rotation import validate_rotation


def report(state, at=NOW):
    checks = [{"client": e.client, "server": e.server,
               "errors": edge_errors(state, e, at)} for e in edges()]
    return {"required_edges": len(checks),
            "verified_edges": sum(not c["errors"] for c in checks),
            "failed_edges": sum(bool(c["errors"]) for c in checks),
            "verification_disabled": sum(not p.verify_peer for p in state.values()),
            "old_identities": sum(p.leaf.issuer != NEW for p in state.values()),
            "checks": checks}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["incident", "rollback", "expand-trust", "safe-plan", "unsafe-plan"])
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    if a.mode in {"safe-plan", "unsafe-plan"}:
        steps = safe_plan() if a.mode == "safe-plan" else rotate_first_plan()
        verdict = validate_rotation(baseline(), edges(), steps, now=NOW,
                                    approved_roots=APPROVED, target_root=NEW)
        state = baseline()
        snapshots = []
        for i, step in enumerate(steps):
            state = apply_step(state, step)
            snapshots.append({"step": i, **report(state, step.at)})
        output = {"accepted": verdict.accepted, "reason": verdict.reason,
                  "first_unsafe_step": verdict.step_index, "snapshots": snapshots}
        if a.mode == "safe-plan":
            expected_ok = verdict.accepted and all(s["failed_edges"] == 0 for s in snapshots) and snapshots[-1]["old_identities"] == 0
        else:
            expected_ok = not verdict.accepted and verdict.step_index == 0
    else:
        state = incident()
        if a.mode == "rollback": state = baseline()
        if a.mode == "expand-trust":
            for c in state:
                state[c] = replace(state[c], trust=APPROVED)
        output = report(state)
        expected_ok = output["failed_edges"] == (2 if a.mode == "incident" else 0)
    print(json.dumps(output, indent=2))
    if a.verify and not expected_ok: raise SystemExit(1)


if __name__ == "__main__": main()
