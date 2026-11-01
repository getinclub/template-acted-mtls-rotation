import copy
import unittest
from dataclasses import replace
from fixtures import APPROVED, NEW, NOW, OLD, baseline, edges, safe_plan, rotate_first_plan
from model import Leaf, Peer, Step
from rotation import validate_rotation

class RotationContract(unittest.TestCase):
    def check(self, plan, state=None, accepted=False, first=None):
        state = baseline() if state is None else state
        original = copy.deepcopy(state)
        result = validate_rotation(state, edges(), plan, now=NOW, approved_roots=APPROVED, target_root=NEW)
        self.assertEqual(result.accepted, accepted, result)
        if first is not None: self.assertEqual(result.step_index, first, result)
        self.assertEqual(state, original, 'validator must not mutate inventory')
        return result
    def test_completed_inventory_still_requires_initial_authentication(self):
        state={n:Peer(Leaf(NEW,n),frozenset({NEW})) for n in baseline()}
        state['orders-1']=replace(state['orders-1'],leaf=Leaf(NEW,'impostor'))
        self.check([],state)
    def test_final_bad_identity_is_not_completion(self):
        self.check(safe_plan()+[Step('orders-1',NOW,leaf=Leaf(NEW,'impostor'))],first=12)
    def test_safe_staged_rotation(self): self.check(safe_plan(), accepted=True)
    def test_rotate_server_before_trust(self): self.check(rotate_first_plan(), first=0)
    def test_rotate_client_before_server_trust(self):
        self.check([Step('checkout-1', NOW, leaf=Leaf(NEW,'checkout-1'))]+safe_plan(), first=0)
    def test_temporary_disabled_verification_is_not_safe(self):
        self.check([Step('orders-1',NOW,verify_peer=False),Step('orders-1',NOW,verify_peer=True)]+safe_plan(), first=0)
    def test_temporary_wrong_server_identity(self):
        self.check([Step('orders-1',NOW,leaf=Leaf(OLD,'impostor')),Step('orders-1',NOW,leaf=Leaf(OLD,'orders-1'))]+safe_plan(), first=0)
    def test_temporary_wrong_client_identity(self):
        self.check([Step('checkout-1',NOW,leaf=Leaf(OLD,'other-client')),Step('checkout-1',NOW,leaf=Leaf(OLD,'checkout-1'))]+safe_plan(), first=0)
    def test_intermediate_expired_leaf(self):
        self.check([Step('orders-1',NOW,leaf=Leaf(OLD,'orders-1',0,9)),Step('orders-1',NOW,leaf=Leaf(OLD,'orders-1'))]+safe_plan(), first=0)
    def test_intermediate_not_yet_valid(self):
        self.check([Step('orders-1',NOW,leaf=Leaf(OLD,'orders-1',11,100)),Step('orders-1',NOW,leaf=Leaf(OLD,'orders-1'))]+safe_plan(), first=0)
    def test_unapproved_trust_even_when_removed_later(self):
        self.check([Step('orders-1',NOW,trust=APPROVED|{'unapproved'}),Step('orders-1',NOW,trust=frozenset({OLD}))]+safe_plan(), first=0)
    def test_empty_trust_temporarily(self):
        self.check([Step('orders-1',NOW,trust=frozenset()),Step('orders-1',NOW,trust=frozenset({OLD}))]+safe_plan(), first=0)
    def test_premature_contraction(self):
        p=safe_plan(); self.check(p[:4]+[Step('orders-1',NOW,trust=frozenset({NEW}))]+p[4:], first=4)
    def test_incomplete_rotation_rejected(self): self.check(safe_plan()[:8])
    def test_no_op_does_not_complete(self): self.check([])
    def test_unknown_peer(self): self.check([Step('ghost',NOW)]+safe_plan(), first=0)
    def test_time_must_not_move_backward(self): self.check([Step('orders-1',9)]+safe_plan(), first=0)
    def test_initial_incident_requires_containment_first(self):
        state=baseline(); state['orders-2']=replace(state['orders-2'],leaf=Leaf(NEW,'orders-2'))
        self.check(safe_plan(state),state)
    def test_offline_inventory_identity_must_migrate(self):
        state=baseline(); state['offline-worker']=Peer(Leaf(OLD,'offline-worker'),frozenset({OLD}))
        self.check(safe_plan(),state)
    def test_offline_inventory_migrates(self):
        state=baseline(); state['offline-worker']=Peer(Leaf(OLD,'offline-worker'),frozenset({OLD}))
        self.check(safe_plan(state),state,accepted=True)
    def test_delayed_replacement_cannot_hide_expiry_gap(self):
        state=baseline(); state['orders-1']=replace(state['orders-1'],leaf=Leaf(OLD,'orders-1',0,12))
        p=[Step('orders-1',15,leaf=Leaf(OLD,'orders-1',0,100))]+safe_plan(at=15)
        self.check(p,state,first=0)
    def test_dormant_straggler_blocks_root_retirement(self):
        state=baseline(); state['offline-worker']=Peer(Leaf(OLD,'offline-worker'),frozenset({OLD}))
        p=safe_plan()+[Step('offline-worker',NOW,trust=APPROVED),Step('offline-worker',NOW,leaf=Leaf(NEW,'offline-worker')),Step('offline-worker',NOW,trust=frozenset({NEW}))]
        self.check(p,state,first=8)
    def test_unapproved_target_rejected(self):
        r=validate_rotation(baseline(),edges(),safe_plan(),now=NOW,approved_roots=APPROVED,target_root='evil')
        self.assertFalse(r.accepted)
    def test_permutations_within_safe_stages(self):
        import itertools
        p=safe_plan()
        for order in itertools.permutations(range(4)):
            with self.subTest(order=order):
                self.check([p[i] for i in order]+[p[4+i] for i in order]+[p[8+i] for i in order],accepted=True)
    def test_validity_boundary_is_inclusive(self):
        self.check(safe_plan(at=100),accepted=True)
    def test_later_step_expires_untouched_peers(self):
        self.check([Step('checkout-1',101,leaf=Leaf(OLD,'checkout-1',0,200))]+safe_plan(at=101),first=0)

if __name__=='__main__': unittest.main()
