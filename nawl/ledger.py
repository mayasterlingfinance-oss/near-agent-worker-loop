"""Append-only JSONL ledger: every bid, delivery and on-chain balance snapshot."""
import json
import os
import time


class Ledger:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def add(self, kind, **data):
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind, **data}
        with open(self.path, "a") as f:
            f.write(json.dumps(row) + "\n")
        return row

    def rows(self, kind=None):
        if not os.path.exists(self.path):
            return []
        out = [json.loads(l) for l in open(self.path) if l.strip()]
        return [r for r in out if kind is None or r["kind"] == kind]

    def verified_revenue_usdc(self):
        """Revenue counts only as on-chain USDC balance growth between snapshots."""
        snaps = self.rows("snapshot")
        if len(snaps) < 2:
            return 0.0
        return round(max(0.0, snaps[-1]["usdc"] - snaps[0]["usdc"]), 6)
