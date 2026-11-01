"""Trusted lab state, not X.509 parsing, signature verification or a TLS stack."""
from dataclasses import dataclass, replace
from typing import Mapping


@dataclass(frozen=True)
class Leaf:
    issuer: str
    identity: str
    not_before: int = 0
    not_after: int = 100


@dataclass(frozen=True)
class Peer:
    leaf: Leaf
    trust: frozenset[str]
    verify_peer: bool = True


@dataclass(frozen=True)
class Edge:
    client: str
    server: str
    client_identity: str
    server_identity: str


@dataclass(frozen=True)
class Step:
    peer: str
    at: int
    leaf: Leaf | None = None
    trust: frozenset[str] | None = None
    verify_peer: bool | None = None


@dataclass(frozen=True)
class Verdict:
    accepted: bool
    reason: str
    step_index: int | None = None


def apply_step(state: Mapping[str, Peer], step: Step) -> dict[str, Peer]:
    """Copy-on-write update of one peer; caller performs safety checks afterward."""
    if step.peer not in state:
        raise ValueError("unknown peer")
    peer = state[step.peer]
    result = dict(state)
    result[step.peer] = replace(peer,
        leaf=peer.leaf if step.leaf is None else step.leaf,
        trust=peer.trust if step.trust is None else step.trust,
        verify_peer=peer.verify_peer if step.verify_peer is None else step.verify_peer)
    return result


def edge_errors(state: Mapping[str, Peer], edge: Edge, at: int) -> list[str]:
    client, server = state[edge.client], state[edge.server]
    errors = []
    for name, peer in ((edge.client, client), (edge.server, server)):
        if not peer.verify_peer:
            errors.append(f"{name}: peer verification disabled")
        if not peer.leaf.not_before <= at <= peer.leaf.not_after:
            errors.append(f"{name}: identity outside validity interval")
    if client.leaf.identity != edge.client_identity:
        errors.append(f"{edge.client}: unexpected client identity")
    if server.leaf.identity != edge.server_identity:
        errors.append(f"{edge.server}: unexpected server identity")
    if server.leaf.issuer not in client.trust:
        errors.append(f"{edge.client}: does not trust server issuer")
    if client.leaf.issuer not in server.trust:
        errors.append(f"{edge.server}: does not trust client issuer")
    return errors


def fleet_errors(state, edges, at, approved_roots):
    errors = []
    for name, peer in state.items():
        if not peer.verify_peer:
            errors.append(f"{name}: verification disabled")
        if not peer.trust or not peer.trust <= approved_roots:
            errors.append(f"{name}: trust contains unapproved roots or is empty")
        if peer.leaf.issuer not in approved_roots:
            errors.append(f"{name}: unapproved issuer")
        if not peer.leaf.not_before <= at <= peer.leaf.not_after:
            errors.append(f"{name}: expired or not yet valid")
    for edge in edges:
        errors.extend(edge_errors(state, edge, at))
    return errors


def final_complete(state, target_root):
    return all(p.leaf.issuer == target_root and p.trust == frozenset({target_root})
               and p.verify_peer for p in state.values())
