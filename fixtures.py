from dataclasses import replace
from model import Leaf, Peer, Edge, Step

OLD = "root-2026-a"
NEW = "root-2026-b"
APPROVED = frozenset({OLD, NEW})
NOW = 10


def baseline():
    return {name: Peer(Leaf(OLD, name), frozenset({OLD}))
            for name in ("checkout-1", "checkout-2", "orders-1", "orders-2")}


def edges():
    return [Edge(c, s, c, s) for c in ("checkout-1", "checkout-2")
            for s in ("orders-1", "orders-2")]


def safe_plan(state=None, at=NOW):
    state = baseline() if state is None else state
    names = list(state)
    return ([Step(n, at, trust=APPROVED) for n in names]
            + [Step(n, at, leaf=replace(state[n].leaf, issuer=NEW)) for n in names]
            + [Step(n, at, trust=frozenset({NEW})) for n in names])


def rotate_first_plan():
    plan = safe_plan()
    # Rotate one server before either client has loaded its new trust anchor.
    first = next(s for s in plan if s.peer == "orders-2" and s.leaf is not None)
    return [first] + [s for s in plan if s is not first]


def incident():
    state = baseline()
    state["orders-2"] = replace(state["orders-2"], leaf=Leaf(NEW, "orders-2"))
    return state
