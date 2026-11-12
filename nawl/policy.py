"""Guardrails every outgoing action passes through.

The point of this module: an autonomous agent that earns money must not
pretend to be human, must not spam bids, and must not take work it cannot do.
These checks are deterministic, so a judge or an operator can read them.
"""
from dataclasses import dataclass, field

DISCLOSURE = "Disclosure: I am an autonomous AI agent"


@dataclass
class Policy:
    min_budget_usdc: float = 1.0          # skip dust jobs
    max_open_bids: int = 5                # no bid spraying
    max_bid_usdc: float = 100.0           # never quote above this without the operator
    allowed_tokens: tuple = ("USDC",)
    keywords: tuple = ("research", "report", "analysis", "survey", "compare",
                       "marketplace", "x402", "agent", "mcp", "pricing", "data")
    blocked: tuple = ("book a", "order a", "call-for-me", "uber eats", "photo",
                      "physical", "in person", "kyc", "identity verified",
               "build it and list it")
    verification_held: str = "none"       # badge the owner holds

    def fit(self, job: dict) -> tuple[float, list[str]]:
        """Return (score 0..1, reasons). Score 0 means: do not bid."""
        reasons = []
        title = (job.get("title") or "").lower()
        desc = (job.get("description") or "").lower()
        text = title + " " + desc
        try:
            budget = float(job.get("budgetAmount") or 0)
        except ValueError:
            budget = 0.0
        if job.get("budgetToken") not in self.allowed_tokens:
            return 0.0, [f"token {job.get('budgetToken')} not accepted"]
        if budget < self.min_budget_usdc:
            return 0.0, [f"budget {budget} below floor {self.min_budget_usdc}"]
        need = job.get("minBuilderVerification") or "none"
        if need != "none" and need != self.verification_held:
            return 0.0, [f"needs builder badge '{need}'"]
        for b in self.blocked:
            if b in text:
                return 0.0, [f"needs a human or physical action ('{b}')"]
        hits = [k for k in self.keywords if k in text]
        if not hits:
            return 0.0, ["no capability match"]
        score = min(1.0, 0.2 + 0.1 * len(hits) + min(budget, 50) / 100)
        reasons.append(f"keywords: {', '.join(hits[:6])}")
        reasons.append(f"budget {budget:g} {job.get('budgetToken')}")
        return round(score, 2), reasons

    def check_bid(self, amount: float, proposal: str, open_bids: int) -> list[str]:
        """Return a list of violations; empty means the bid may go out."""
        v = []
        if not proposal.strip().startswith(DISCLOSURE):
            v.append("proposal must open with the AI disclosure")
        if amount > self.max_bid_usdc:
            v.append(f"amount {amount} above max {self.max_bid_usdc}")
        if amount <= 0:
            v.append("amount must be positive")
        if open_bids >= self.max_open_bids:
            v.append(f"already {open_bids} open bids (max {self.max_open_bids})")
        return v
