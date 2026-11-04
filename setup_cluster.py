#!/usr/bin/env python3
"""Load data, create data views, create detection rules and the 10 Cases.

Usage:
  pip install requests
  set ES_URL=https://<es-endpoint>  KIBANA_URL=https://<kibana-endpoint>  API_KEY=<encoded admin api key>
  python generate_data.py
  python setup_cluster.py            # everything
  python setup_cluster.py --only cases --recreate-cases
  python setup_cluster.py --update-case Q1
  python setup_cluster.py --only data --index pubsec-potholes
Flags: --only {data,views,settings,rules,disable-rules,cases}  --recreate-cases  --update-case Q#
       --index <index>  --owner cases|observability|securitySolution
"""
import argparse, glob, json, os, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TAG = "pubsec-game"

MAPPINGS = {
    "pubsec-potholes": {"@timestamp": {"type": "date"}, "council": {"type": "keyword"},
                        "severity": {"type": "keyword"}, "location": {"type": "geo_point"},
                        "nickname": {"type": "keyword"}, "status": {"type": "keyword"},
                        "description": {"type": "text"}, "width_cm": {"type": "integer"}},
    "pubsec-canteen": {"@timestamp": {"type": "date"}, "department": {"type": "keyword"},
                       "biscuit": {"type": "keyword"}, "packets": {"type": "integer"},
                       "meeting_type": {"type": "keyword"}},
    "pubsec-planning": {"@timestamp": {"type": "date"}, "reference": {"type": "keyword"},
                        "council": {"type": "keyword"}, "address": {"type": "text"},
                        "description": {"type": "text"}, "applicant_name": {"type": "keyword"},
                        "decision": {"type": "keyword"}},
    "pubsec-gritters": {"@timestamp": {"type": "date"}, "gritter": {"type": "keyword"},
                        "depot": {"type": "keyword"}, "km_gritted": {"type": "float"},
                        "salt_tonnes": {"type": "float"}},
    "pubsec-endpoint": {"@timestamp": {"type": "date"}, "message": {"type": "text"},
                        "host": {"properties": {"name": {"type": "keyword"}}},
                        "user": {"properties": {"name": {"type": "keyword"}}},
                        "event": {"properties": {"category": {"type": "keyword"}, "action": {"type": "keyword"},
                                                 "kind": {"type": "keyword"}}},
                        "process": {"properties": {"name": {"type": "keyword"}, "command_line": {"type": "wildcard"},
                                                   "parent": {"properties": {"name": {"type": "keyword"}}}}},
                        "file": {"properties": {"name": {"type": "keyword"}, "extension": {"type": "keyword"}}},
                        "network": {"properties": {"bytes": {"type": "long"}}},
                        "destination": {"properties": {"domain": {"type": "keyword"}, "ip": {"type": "ip"}}}},
    "pubsec-portal": {"@timestamp": {"type": "date"}, "service": {"type": "keyword"},
                      "http": {"properties": {"response": {"properties": {"status_code": {"type": "integer"}}}}},
                      "response_time_ms": {"type": "integer"},
                      "client": {"properties": {"country": {"type": "keyword"}}}},
}


_orig_rfs = requests.Response.raise_for_status


def _rfs(self):  # show the server's error message, not just the status code
    if self.status_code >= 400:
        print(f"ERROR {self.status_code} {self.request.method} {self.url}\n{self.text[:600]}")
    return _orig_rfs(self)


requests.Response.raise_for_status = _rfs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--es-url", default=os.getenv("ES_URL"))
    ap.add_argument("--kibana-url", default=os.getenv("KIBANA_URL"))
    ap.add_argument("--api-key", default=os.getenv("API_KEY"))
    ap.add_argument("--only", choices=["data", "views", "settings", "rules", "disable-rules", "cases"])
    ap.add_argument("--recreate-cases", action="store_true")
    ap.add_argument("--owner", default="cases")
    ap.add_argument("--update-case", help="update only this case's description, e.g. Q1")
    ap.add_argument("--index", help="with --only data: reload just this index, e.g. pubsec-potholes")
    a = ap.parse_args()
    if not (a.es_url and a.kibana_url and a.api_key):
        sys.exit("Need ES_URL, KIBANA_URL and API_KEY (env vars or flags)")
    kb = a.kibana_url.rstrip("/")
    es = a.es_url.rstrip("/")
    H = {"Authorization": f"ApiKey {a.api_key}", "Content-Type": "application/json"}
    KH = dict(H, **{"kbn-xsrf": "true"})
    run = lambda s: a.only in (None, s)

    if a.update_case:  # patch ONE case's description in place, leaving every other case untouched
        sys.path.insert(0, HERE)
        from cases_content import build_cases
        prefix = a.update_case + " |"
        new = next(c for c in build_cases(kb) if c["title"].startswith(prefix))
        found = requests.get(f"{kb}/api/cases/_find", headers=KH,
                             params={"perPage": 100, "owner": a.owner}).json()
        match = [c for c in found.get("cases", []) if c["title"].startswith(prefix)]
        if len(match) != 1:
            sys.exit(f"Expected exactly one case starting with '{prefix}', found {len(match)}")
        r = requests.patch(f"{kb}/api/cases", headers=KH, json={"cases": [
            {"id": match[0]["id"], "version": match[0]["version"], "description": new["description"]}]})
        r.raise_for_status()
        print("updated description of:", match[0]["title"])
        return

    if run("data"):
        for idx, props in MAPPINGS.items():
            if a.index and idx != a.index:
                continue
            requests.delete(f"{es}/{idx}", headers=H)
            r = requests.put(f"{es}/{idx}", headers=H, json={
                "mappings": {"properties": props}})
            r.raise_for_status()
        for path in sorted(glob.glob(os.path.join(HERE, "data", "*.ndjson"))):
            if a.index and os.path.basename(path) != a.index + ".ndjson":
                continue
            lines = open(path, encoding="utf-8").read().splitlines()
            for i in range(0, len(lines), 10000):  # even number of lines per chunk
                body = "\n".join(lines[i:i + 10000]) + "\n"
                r = requests.post(f"{es}/_bulk", headers=dict(H, **{"Content-Type": "application/x-ndjson"}),
                                  data=body.encode("utf-8"))
                r.raise_for_status()
                if r.json().get("errors"):
                    sys.exit(f"Bulk errors in {path}: {r.text[:500]}")
            print("loaded", os.path.basename(path))
        requests.post(f"{es}/pubsec-*/_refresh", headers=H)

    if run("views"):
        for idx in MAPPINGS:
            r = requests.post(f"{kb}/api/data_views/data_view", headers=KH, json={
                "override": True,
                "data_view": {"id": idx, "title": idx, "name": idx, "timeFieldName": "@timestamp"}})
            r.raise_for_status()
            print("data view", idx)

    if run("settings"):
        tp = json.dumps({"from": "2026-01-01T00:00:00.000Z", "to": "2026-04-01T00:00:00.000Z"})
        r = requests.post(f"{kb}/api/kibana/settings", headers=KH,
                          json={"changes": {"timepicker:timeDefaults": tp}})
        if r.status_code < 400:
            print("default time range set to Jan 1 - Apr 1 2026")
        else:
            print("WARNING: could not set default time range:", r.status_code, r.text[:400])
            print("Set it by hand: Stack Management > Advanced settings > 'Time filter defaults' "
                  '= {"from":"2026-01-01T00:00:00.000Z","to":"2026-04-01T00:00:00.000Z"}')

    if run("rules"):
        # Custom-query detection rules over the static endpoint data. Lookback covers Jan-Mar 2026.
        # Alerts are created when the rules first run; --disable-rules switches them off afterwards
        # so the alert set stays frozen for the event.
        rules = [
            ("pubsec-macro-doc-opened", "Macro-enabled document opened from email", 47,
             'event.action : "attachment_opened" and file.extension : ("docm" or "xlsm")'),
            ("pubsec-office-spawns-powershell", "Office application spawned encoded PowerShell", 73,
             'process.parent.name : ("WINWORD.EXE" or "EXCEL.EXE") and process.name : "powershell.exe" '
             'and process.command_line : *-enc*'),
            ("pubsec-schtask-from-powershell", "Scheduled task created by PowerShell", 47,
             'event.action : "scheduled_task_created" and process.parent.name : "powershell.exe"'),
            ("pubsec-lsass-access", "Suspicious LSASS memory access", 73,
             'event.action : "lsass_access"'),
            ("pubsec-large-exfil", "Large outbound transfer to rare domain", 73,
             'event.action : "network_connection" and network.bytes > 1000000000'),
        ]
        for rid, name, risk, q in rules:
            body = {"rule_id": rid, "name": name, "description": f"{name} (Case Files game)",
                    "type": "query", "language": "kuery", "query": q, "index": ["pubsec-endpoint"],
                    "risk_score": risk, "severity": "high" if risk >= 70 else "medium",
                    "interval": "5m", "from": "now-400d", "enabled": True, "tags": [TAG]}
            requests.delete(f"{kb}/api/detection_engine/rules", headers=KH, params={"rule_id": rid})
            r = requests.post(f"{kb}/api/detection_engine/rules", headers=KH, json=body)
            r.raise_for_status()
            print("rule", name)
        print("Wait ~10 min, check Security > Alerts shows 5 alerts, then run: "
              "python setup_cluster.py --only disable-rules")

    if a.only == "disable-rules":
        r = requests.post(f"{kb}/api/detection_engine/rules/_bulk_action", headers=KH, json={
            "action": "disable", "query": f"alert.attributes.tags: \"{TAG}\""})
        r.raise_for_status()
        print("rules disabled")

    if run("cases"):
        sys.path.insert(0, HERE)
        from cases_content import build_cases
        found = requests.get(f"{kb}/api/cases/_find", headers=KH,
                             params={"tags": TAG, "perPage": 100, "owner": a.owner}).json()
        old = [c["id"] for c in found.get("cases", [])]
        if old and not a.recreate_cases:
            sys.exit(f"{len(old)} game cases already exist. Use --recreate-cases to replace them.")
        if old:
            requests.delete(f"{kb}/api/cases", headers=KH, params={"ids": json.dumps(old)}).raise_for_status()
        for case in build_cases(kb):
            r = requests.post(f"{kb}/api/cases", headers=KH, json={
                "title": case["title"], "description": case["description"], "tags": [TAG],
                "owner": a.owner, "severity": "low", "assignees": [],
                "settings": {"syncAlerts": False},
                "connector": {"id": "none", "name": "none", "type": ".none", "fields": None}})
            r.raise_for_status()
            cid = r.json()["id"]
            for text in case["comments"]:
                requests.post(f"{kb}/api/cases/{cid}/comments", headers=KH,
                              json={"type": "user", "comment": text, "owner": a.owner}).raise_for_status()
            print("case", case["title"])


if __name__ == "__main__":
    main()
