"""nawl: board -> fit -> guarded bid -> deliver -> verify payout on NEAR."""
import argparse
import json
import os
import sys

from .ledger import Ledger
from .market import Market
from .near import near_balance, usdc_balance
from .policy import Policy


def _market():
    tok = os.environ.get("AGENT_API_TOKEN")
    if not tok:
        sys.exit("set AGENT_API_TOKEN (an aat_ token for your agent)")
    return Market(tok)


def cmd_board(a, pol, led):
    jobs = _market().board(kind=a.kind)
    rows = []
    for j in jobs:
        s, why = pol.fit(j)
        rows.append((s, j, why))
    rows.sort(key=lambda r: -r[0])
    for s, j, why in rows:
        if s == 0 and not a.all:
            continue
        print(f"{s:4.2f}  {j.get('budgetAmount')!s:>8} {j.get('budgetToken')}  {j['jobId']}  {j['title'][:70]}")
        print(f"      {'; '.join(why)}")
    print(f"\n{len(jobs)} jobs on the board, {sum(1 for r in rows if r[0] > 0)} fit the policy")


def cmd_bid(a, pol, led):
    m = _market()
    proposal = open(a.proposal_file).read()
    bids = m.my_bids()
    open_bids = sum(1 for b in (bids.get("bids", bids) if isinstance(bids, dict) else bids)
                    if (b.get("status") in (None, "pending", "open")))
    v = pol.check_bid(a.amount, proposal, open_bids)
    if v:
        sys.exit("refused by policy: " + "; ".join(v))
    r = m.bid(a.job, a.amount, proposal)
    led.add("bid", job=a.job, amount=a.amount, bid_id=r.get("bidId"))
    print(json.dumps(r, indent=1)[:800])


def cmd_assignments(a, pol, led):
    for row in _market().assignments():
        asg = row.get("assignment", row)
        print(asg.get("assignmentId"), asg.get("status"), (row.get("job") or {}).get("title", "")[:70])


def cmd_submit(a, pol, led):
    md = open(a.file).read()
    if "AI agent" not in md[:600]:
        sys.exit("refused by policy: deliverable must state AI authorship near the top")
    r = _market().submit(a.assignment, md)
    led.add("submit", assignment=a.assignment, words=len(md.split()))
    print(json.dumps(r, indent=1)[:800])


def cmd_payout(a, pol, led):
    u, n = usdc_balance(a.account), near_balance(a.account)
    led.add("snapshot", account=a.account, usdc=u, near=n)
    print(f"{a.account}: {u:.6f} USDC, {n:.5f} NEAR (mainnet, read via public RPC)")
    print(f"verified revenue since first snapshot: {led.verified_revenue_usdc():.6f} USDC")


def main(argv=None):
    p = argparse.ArgumentParser(prog="nawl", description=__doc__)
    p.add_argument("--ledger", default=os.environ.get("NAWL_LEDGER", "ledger.jsonl"))
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("board"); b.add_argument("--kind", choices=["standard", "competition"]); b.add_argument("--all", action="store_true")
    b.set_defaults(f=cmd_board)
    s = sub.add_parser("bid"); s.add_argument("job"); s.add_argument("--amount", type=float, required=True); s.add_argument("--proposal-file", required=True)
    s.set_defaults(f=cmd_bid)
    sub.add_parser("assignments").set_defaults(f=cmd_assignments)
    d = sub.add_parser("submit"); d.add_argument("assignment"); d.add_argument("--file", required=True)
    d.set_defaults(f=cmd_submit)
    o = sub.add_parser("payout-check"); o.add_argument("account", help="NEAR account, e.g. team.near or a 64-hex implicit account")
    o.set_defaults(f=cmd_payout)
    a = p.parse_args(argv)
    a.f(a, Policy(), Ledger(a.ledger))


if __name__ == "__main__":
    main()
