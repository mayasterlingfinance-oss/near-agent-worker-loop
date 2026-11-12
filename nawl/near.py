"""Read-only NEAR mainnet checks: did the money actually arrive?

Uses only the public JSON-RPC (no keys). USDC on NEAR is the NEP-141 token
17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1 (6 decimals).
"""
import base64
import json
import urllib.request

RPC = "https://rpc.mainnet.near.org"
USDC = "17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1"


def _rpc(method, params, rpc=RPC, opener=urllib.request.urlopen):
    body = json.dumps({"jsonrpc": "2.0", "id": "nawl", "method": method, "params": params}).encode()
    req = urllib.request.Request(rpc, data=body, headers={"Content-Type": "application/json"})
    with opener(req, timeout=30) as r:
        d = json.loads(r.read())
    if "error" in d:
        raise RuntimeError(d["error"])
    return d["result"]


def view(contract, method, args, **kw):
    res = _rpc("query", {"request_type": "call_function", "finality": "final",
                         "account_id": contract, "method_name": method,
                         "args_base64": base64.b64encode(json.dumps(args).encode()).decode()}, **kw)
    return json.loads(bytes(res["result"]).decode())


def usdc_balance(account_id, **kw) -> float:
    raw = view(USDC, "ft_balance_of", {"account_id": account_id}, **kw)
    return int(raw) / 1_000_000


def near_balance(account_id, **kw) -> float:
    try:
        res = _rpc("query", {"request_type": "view_account", "finality": "final",
                             "account_id": account_id}, **kw)
    except RuntimeError:
        return 0.0   # implicit account not yet created on chain
    return int(res["amount"]) / 1e24
