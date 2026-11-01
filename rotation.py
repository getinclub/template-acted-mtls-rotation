"""Edit only validate_rotation. No network or real certificates are used."""
from model import Verdict, apply_step, fleet_errors, final_complete


def validate_rotation(initial, edges, steps, *, now, approved_roots, target_root):
    """Accept only a safe, complete rotation. See README for the full contract.

    BUG: a green final snapshot does not prove the rollout stayed available.
    """
    state = dict(initial)
    if target_root not in approved_roots:
        return Verdict(False, "target root not approved")
    if fleet_errors(state, edges, now, approved_roots):
        return Verdict(False, "unsafe initial inventory")
    at = now
    for index, step in enumerate(steps):
        if step.at < at:
            return Verdict(False, "time moved backward", index)
        at = step.at
        try:
            state = apply_step(state, step)
        except ValueError as exc:
            return Verdict(False, str(exc), index)
    if fleet_errors(state, edges, at, approved_roots):
        return Verdict(False, "unsafe final state")
    if not final_complete(state, target_root):
        return Verdict(False, "rotation incomplete")
    return Verdict(True, "final state is green")
