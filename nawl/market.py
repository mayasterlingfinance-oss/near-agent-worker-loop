"""Minimal client for the NEAR Agent Market worker API (https://market.near.ai/openapi.json)."""
import json
import urllib.request

BASE = "https://market.near.ai"


class Market:
    def __init__(self, token: str, base: str = BASE, opener=None):
        self.token = token
        self.base = base.rstrip("/")
        self._open = opener or urllib.request.urlopen

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with self._open(req, timeout=30) as r:
            raw = r.read()
        return json.loads(raw) if raw else {}

    def board(self, kind=None, limit=50):
        q = f"?limit={limit}" + (f"&kind={kind}" if kind else "")
        return self._req("GET", "/v1/jobs/board" + q).get("jobs", [])

    def my_bids(self):
        return self._req("GET", "/v1/agents/me/bids")

    def assignments(self):
        return self._req("GET", "/v1/agents/me/assignments").get("assignments", [])

    def bid(self, job_id, amount, proposal, sla_seconds=86400):
        return self._req("POST", f"/v1/jobs/{job_id}/bids",
                         {"amount": f"{amount:.2f}", "proposal": proposal, "slaSeconds": sla_seconds})

    def enter(self, job_id):
        return self._req("POST", f"/v1/jobs/{job_id}/entries", {})

    def start(self, assignment_id):
        return self._req("POST", f"/v1/assignments/{assignment_id}/start", {})

    def submit(self, assignment_id, markdown):
        return self._req("POST", f"/v1/assignments/{assignment_id}/submit",
                         {"deliverableMarkdown": markdown})
