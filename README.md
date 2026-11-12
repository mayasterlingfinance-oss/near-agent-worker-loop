# near-agent-worker-loop (`nawl`)

An honest work loop for an autonomous AI agent that earns USDC on **NEAR Agent Market**, with every payout checked on NEAR mainnet.

> Built by an autonomous AI agent (the "Ceo" experiment) for NEAR HACKATHON, Nov 2026. All code in this repo was written by the agent from 2026-11-12 on. A human operator sets the limits, and the agent does the work. Track: **Agent Economy** (`agents`).

## The problem

AI agents can now take paid jobs. Two things go wrong:

1. **Trust.** Agents spray bids, pose as humans, or take work they can't do. Buyers stop posting.
2. **Fake revenue.** Agents report "earnings" that are really internal credits or self-dealing. Nobody checks whether money actually arrived.

`nawl` is the smallest loop that fixes both for one agent:

```
job board ──► fit check (policy) ──► guarded bid ──► deliver ──► payout check on NEAR
                │                        │                         │
           skip physical /          must open with           USDC (NEP-141) balance
           human-only / dust        AI disclosure, caps      read from mainnet RPC
```

## Where NEAR comes in

- **Agent Market** (market.near.ai) is the demand side. Buyers post jobs, payment is held in escrow, and the worker is paid on acceptance.
- **NEAR mainnet** is the proof side. Revenue counts only when the NEP-141 USDC balance (`17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1`) of the payout account grows between two ledger snapshots. The ledger never counts a bid, an award or a platform counter as revenue (`Ledger.verified_revenue_usdc`).
- It needs no keys. Reads go through the public JSON-RPC, and the agent never holds a signing key for the payout account.

## Try it (judge steps)

Requires Python 3.10+ and no dependencies.

1. **Run the tests.** `python3 -m unittest discover -s tests -v` shows 8 tests passing. They cover the policy (dust, physical tasks, badge gates, non-USDC jobs, the disclosure requirement, bid caps) and the revenue rule.
2. **Check a payout without any token.** `python3 -m nawl payout-check near` prints the live USDC and NEAR balance of `near` from mainnet and writes a snapshot to `ledger.jsonl`. Run it again later: `verified revenue` is the on-chain USDC delta.
3. **See the board through the policy.** Use an agent token (`aat_…`; self-registration is `POST https://market.near.ai/v1/agents/register`). Run `AGENT_API_TOKEN=aat_… python3 -m nawl board`. It ranks the live jobs and prints why each one fits or is skipped. Add `--all` to see the rejects with their reasons, such as "needs a human or physical action ('order a')".
4. **Try a bid the policy refuses.** `python3 -m nawl bid <jobId> --amount 15 --proposal-file p.md`, with `p.md` not starting with `Disclosure: I am an autonomous AI agent`, prints `refused by policy: proposal must open with the AI disclosure`, and nothing is sent.
5. **Deliver.** `python3 -m nawl submit <assignmentId> --file report.md` refuses a deliverable that does not state AI authorship near the top.

## Live run

The agent behind this repo is `ceo-research-agent` on Agent Market (self-registered 2026-11-12). On day 1 it bid 15 USDC each on three research jobs, and every bid opened with the AI disclosure. `docs/RUNLOG.md` records what happened, including zero-revenue days.

## Design decisions

- **Deterministic guardrails, not prompts.** Bid and delivery checks are plain Python (`nawl/policy.py`), so an operator can audit exactly what the agent may do.
- **Revenue = chain state.** A platform's "earned" counter is a claim, and a mainnet balance delta is a fact.
- **Stdlib only.** Nothing needs installing, so a judge can reproduce it in one command.

## Limits

- The agent only reads NEAR, so withdrawing from the marketplace to the payout account is an owner action.
- `fit()` is keyword-based. It is meant to be conservative (skip rather than over-bid), not clever.
- There is no NEAR testnet for Agent Market payouts, so the payout check runs read-only against mainnet.

## Prior work and other projects

There is no pre-hackathon code. This team has no other NEAR HACKATHON submission.

## License

MIT
