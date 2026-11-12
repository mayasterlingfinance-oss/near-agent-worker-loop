import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nawl.policy import Policy, DISCLOSURE
from nawl.ledger import Ledger


class PolicyTest(unittest.TestCase):
    def setUp(self):
        self.p = Policy()

    def job(self, **kw):
        j = {"title": "Research report on x402 agent payments", "description": "survey the market",
             "budgetAmount": "15", "budgetToken": "USDC", "minBuilderVerification": "none"}
        j.update(kw); return j

    def test_fit_research_job(self):
        s, why = self.p.fit(self.job())
        self.assertGreater(s, 0)

    def test_reject_dust(self):
        self.assertEqual(self.p.fit(self.job(budgetAmount="0.01"))[0], 0)

    def test_reject_physical(self):
        self.assertEqual(self.p.fit(self.job(title="Order a burger via Uber Eats"))[0], 0)

    def test_reject_badge(self):
        self.assertEqual(self.p.fit(self.job(minBuilderVerification="identity_verified"))[0], 0)

    def test_reject_non_usdc(self):
        self.assertEqual(self.p.fit(self.job(budgetToken="USD"))[0], 0)

    def test_bid_needs_disclosure(self):
        self.assertTrue(self.p.check_bid(15, "Hi, I'm Bob, a researcher", 0))
        self.assertFalse(self.p.check_bid(15, DISCLOSURE + " (demo).", 0))

    def test_bid_caps(self):
        self.assertTrue(self.p.check_bid(500, DISCLOSURE, 0))
        self.assertTrue(self.p.check_bid(15, DISCLOSURE, 5))

    def test_revenue_only_from_chain_snapshots(self):
        with tempfile.TemporaryDirectory() as d:
            led = Ledger(os.path.join(d, "l.jsonl"))
            led.add("bid", job="x", amount=15)
            self.assertEqual(led.verified_revenue_usdc(), 0.0)
            led.add("snapshot", account="a.near", usdc=1.0, near=0)
            led.add("snapshot", account="a.near", usdc=15.25, near=0)
            self.assertEqual(led.verified_revenue_usdc(), 14.25)


if __name__ == "__main__":
    unittest.main()
