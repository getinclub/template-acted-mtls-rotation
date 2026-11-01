# The Certificate Rotation That Split the Fleet

**40-minute acted incident · Python 3.12 · no dependencies or cloud account**

Two checkout clients call two orders servers: four required pairings. After a planned certificate rotation, half reject their peer. Your job is to diagnose, contain without bypassing authentication, and repair one rollout-plan validator.

This is a deterministic **state model**, not a TLS library. Issuer names represent authenticated inventory; they are not a substitute for cryptographic verification. No real certificates, secrets, endpoints or network calls are used.

## Start

```sh
python --version
python monitor.py fleet timeline
python monitor.py fleet inventory
python monitor.py fleet matrix
python monitor.py fleet rollback-inventory
python replay.py incident --verify
python -m unittest discover -s tests -v
```

Some tests intentionally fail in the starter. Read the evidence and state your containment preconditions before inspecting remediation fixtures. In the platform, submit the two required checkpoints and final reflection.

## Your change

Edit **only `validate_rotation` in `rotation.py`**. Preserve its signature and return a `Verdict`. Use the provided helpers; no crypto implementation is required. Public tests are executable acceptance criteria, not hidden answers.

Inputs are trusted, well-typed Python dataclasses: nonempty complete inventory, a finite reusable list of required edges whose peers exist, finite list of steps, integer times, and authenticated approved roots. Arbitrary JSON parsing, empty inventories, malformed objects and discovery of missing peers are out of scope. Each step updates one peer atomically; the model has no concurrent updates. All old/new leaves are assumed unrevoked and issued through a secure process.

### Acceptance contract

- Reject an unsafe initial inventory or unapproved target root.
- For each step, reject backward time and unknown peers. Check the previous state at the new time **before** replacement, so a late replacement cannot hide an expiration gap. Check the updated state too.
- At every boundary, require enabled peer verification, approved nonempty trust, approved leaf issuers, current validity and the expected identity on **both** ends of every required edge. A client must trust the server issuer and the server must trust the client issuer.
- Validity endpoints are inclusive; time is a synthetic scalar, not a clock-skew policy.
- Our conservative fleet-retirement policy forbids removing a root from any peer while **any inventoried identity still uses it**, including dormant peers outside the exercised edge list. This policy is deliberately stricter than checking currently exercised connections alone. Rotate that last identity in a prior step, then retire trust.
- Accept only a fully migrated final inventory: every leaf uses the approved target root and every trust bundle contains only that root.
- Return the first unsafe step index (zero-based) for step failures. Initial/final-policy failures have no step index. Do not mutate caller input. Error wording is free; describe useful evidence.

The starter checks the final state but can approve a plan that temporarily breaks authentication. Fix the temporal invariant, not a particular fixture name.

## Verify and submit

```sh
python -m unittest discover -s tests -v
python replay.py safe-plan --verify
python replay.py unsafe-plan --verify
```

`safe-plan` must be accepted; `unsafe-plan` must be rejected at step 0. JSON snapshots are independently calculated by the model; the validator’s answer is separate. A passing final snapshot is not evidence that all earlier states were safe.

Submit a PR with the function fix and a short explanation: evidence of the original failure; chosen containment and remaining old identities; why both trust directions matter; delayed-expiry and dormant-inventory cases; actual test/replay output; a production canary and rollback gate. Do not modify tests, helpers or CI to make the check green.

CI is configured but not executed on GitHub by this package. Repository tests alone are not tamper-proof grading. Platform verification must be tied to the current PR and trusted grading assets.

## Operational boundary

Trust expansion is safe only when the new root is authenticated and approved. Restoring an old leaf is an option only while that identity and key remain valid, approved and uncompromised. This incident is **not** a compromise-response playbook. Containment restores connectivity but does not finish rotation. Production requires proper chain/signature/revocation checks, SAN/identity authorization, trusted time, secure distribution, reload acknowledgement, complete inventory, and full-handshake probes (not just reused sessions or health endpoints).
