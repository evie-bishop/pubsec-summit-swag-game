#!/usr/bin/env python3
"""Datasets + answers for the optional EXPERT ROUND (E1-E6).

Run AFTER generate_data.py (it reads the potholes, endpoint and gritters files that script wrote).
Uses its own seed, so the main game's data, answers and delegate code are not affected.

Mix of tools: E1 Discover (KQL), E2 Discover (investigation), E3 Maps, E4 Lens (formula),
E5 AI agent, E6 ES|QL.

Writes next to this script:
  data/pubsec-auth.ndjson, pubsec-servicedesk.ndjson, pubsec-contracts.ndjson
  answer_key_expert.json      computed answers + the 6-character EXPERT code
  SDR_expert_answer_key.md    SDR-only key with the worked solutions
"""
import json, random, collections, datetime as dt, os, re, sys

rng = random.Random(4242)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

START = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
END = dt.datetime(2026, 4, 1, tzinfo=dt.timezone.utc)
SPAN = (END - START).total_seconds()


def rand_ts():
    return START + dt.timedelta(seconds=rng.random() * SPAN)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def write(index, docs):
    with open(os.path.join(OUT, f"{index}.ndjson"), "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"index": {"_index": index}}) + "\n")
            f.write(json.dumps(d) + "\n")
    print(f"{index}: {len(docs)} docs")


def load(index):
    path = os.path.join(OUT, f"{index}.ndjson")
    if not os.path.exists(path):
        sys.exit(f"{path} missing: run generate_data.py first")
    return [json.loads(l) for l in open(path, encoding="utf-8").read().splitlines()[1::2]]


answers = {}

# ------------------------------------------------------------------ E1: auth (Discover + KQL)
STAFF = ["j.smith", "p.patel", "m.jones", "s.khan", "d.evans", "r.wilson", "k.thomas", "l.walker",
         "a.gresham", "c.bennett", "h.morris", "f.clarke", "g.hughes", "b.edwards", "n.lewis",
         "o.turner", "t.cooper", "e.ward", "i.baker", "u.hill", "m.holloway"]
FOREIGN = ["US", "BR", "IN", "PL", "SG", "NG", "VN"]


def auth(ts, user, country, outcome):
    ip = f"198.51.100.{rng.randint(1, 254)}" if country == "GB" else f"203.0.113.{rng.randint(1, 254)}"
    return {"@timestamp": iso(ts), "user": {"name": user}, "source": {"ip": ip, "geo": {"country_iso_code": country}},
            "event": {"outcome": outcome, "category": "authentication"}}


auth_docs = []
for _ in range(3000):
    auth_docs.append(auth(rand_ts(), rng.choice(STAFF), "GB", "success"))
for _ in range(400):  # failed attempts come from all over: a decoy for anyone who forgets to filter
    auth_docs.append(auth(rand_ts(), rng.choice(STAFF), rng.choice(FOREIGN + ["GB"] * 3), "failure"))
T = dt.datetime(2026, 2, 17, 9, 5, tzinfo=dt.timezone.utc)
auth_docs.append(auth(T, "m.holloway", "GB", "success"))
auth_docs.append(auth(T + dt.timedelta(minutes=35), "m.holloway", "SG", "success"))
rng.shuffle(auth_docs)
write("pubsec-auth", auth_docs)
odd = [d["user"]["name"] for d in auth_docs
       if d["event"]["outcome"] == "success" and d["source"]["geo"]["country_iso_code"] != "GB"]
assert odd == ["m.holloway"], odd
answers["E1"] = odd[0]

# ------------------------------------------------------------------ E2: endpoint pivot (Discover)
endpoint = load("pubsec-endpoint")
task = None
for d in endpoint:
    if d["host"]["name"] == "MINISTRY-LT-07" and d["event"]["action"] == "scheduled_task_created":
        task = re.search(r"/tn (\S+)", d["process"]["command_line"]).group(1)
assert task, "attack chain not found in pubsec-endpoint"
answers["E2"] = task

# ------------------------------------------------------------------ E3: Maps (northernmost catastrophic pothole)
potholes = load("pubsec-potholes")
cat = sorted((p for p in potholes if p["severity"] == "catastrophic"), key=lambda p: -p["location"]["lat"])
assert cat[0]["location"]["lat"] - cat[1]["location"]["lat"] > 0.5, "northernmost pothole must be clear of the rest"
answers["E3"] = cat[0]["nickname"]

# ------------------------------------------------------------------ E4: Lens formula (salt per 100 km by depot)
gritters = load("pubsec-gritters")
salt, km = collections.Counter(), collections.Counter()
for g in gritters:
    salt[g["depot"]] += g["salt_tonnes"]
    km[g["depot"]] += g["km_gritted"]
ratio = sorted(((salt[d] / km[d] * 100, d) for d in salt), reverse=True)
assert ratio[0][0] > ratio[1][0] * 1.01, ratio
answers["E4"] = ratio[0][1]

# ------------------------------------------------------------------ E5: service desk (Elastic AI Agent)
SDEPTS = ["DWP", "DfE", "MoJ", "HMRC", "DVLA", "Home Office", "DfT", "DEFRA"]
SUMM = ["Printer on fire", "Password reset for a Minister", "Teams stuck on connecting", "Lost the shared drive",
        "Mouse eaten by cat", "Biscuit tin inventory failed", "VPN refuses to VPN", "Monitor shows only blue",
        "Spreadsheet has become sentient", "Wi-Fi works only in the lift"]
PRI = ["P1", "P2", "P3", "P4"]
BASE = {"P1": (40, 10), "P2": (120, 30), "P3": (300, 60), "P4": (600, 100)}
desk, p1_sum, p1_n, all_sum, all_n = [], collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
for i in range(1200):
    d = rng.choice(SDEPTS)
    p = rng.choices(PRI, [.15, .2, .3, .35])[0]
    mu, sd = BASE[p]
    if d == "DVLA" and p == "P1":
        mu = 75
    if d == "HMRC" and p != "P1":
        mu, sd = mu * 1.5, sd * 1.5
    mins = max(5, int(rng.gauss(mu, sd)))
    desk.append({"@timestamp": iso(rand_ts()), "ticket": f"TICKET-{1000 + i}", "priority": p, "dept": d,
                 "resolved_in_mins": mins, "summary": rng.choice(SUMM)})
    all_sum[d] += mins
    all_n[d] += 1
    if p == "P1":
        p1_sum[d] += mins
        p1_n[d] += 1
write("pubsec-servicedesk", desk)
p1_avg = sorted(((p1_sum[d] / p1_n[d], d) for d in SDEPTS), reverse=True)
all_avg = sorted(((all_sum[d] / all_n[d], d) for d in SDEPTS), reverse=True)
assert p1_avg[0][0] > p1_avg[1][0] * 1.1, p1_avg
assert all_avg[0][1] != p1_avg[0][1], "overall winner must differ so the P1 filter matters"
slowest_dept = p1_avg[0][1]
# Part 2 depends on part 1: the longest P1 ticket in that department
dept_p1 = sorted((t for t in desk if t["priority"] == "P1" and t["dept"] == slowest_dept),
                 key=lambda t: -t["resolved_in_mins"])
assert dept_p1[0]["resolved_in_mins"] > dept_p1[1]["resolved_in_mins"], "longest ticket must be unique"
E5_TICKET = dept_p1[0]
answers["E5"] = E5_TICKET["summary"]

# ------------------------------------------------------------------ E6: contracts (ES|QL, normalise supplier names)
OTHERS = ["Kestrel Facilities", "Oakhaven Systems", "Pennine Logistics", "Tidewater Security", "Marlow and Finch",
          "Lanternworks", "Ironbridge Civil", "Cobalt Cloud", "Hartley Catering", "Quill Legal Services",
          "Redfern Print", "Saltmarsh Energy", "Thornbury Data", "Ullswater Training", "Vantage Fleet",
          "Wrenfield Recruitment", "Yarrow Cleaning", "Zephyr Telecoms", "Ashgrove Architects", "Beacon Health Supplies",
          "Copperfield Software", "Dunmore Estates", "Elmstead Transport", "Fairhaven Security", "Glenmore Water",
          "Harrowgate Interiors", "Ivybridge IT", "Juniper Print"]
DEPTS_C = ["DWP", "DfE", "MoJ", "HMRC", "DVLA", "Home Office", "DfT", "DEFRA"]
ROUTES = ["open tender", "framework call-off", "direct award"]
contracts = []


def contract(supplier, value):
    return {"@timestamp": iso(rand_ts()), "supplier": supplier, "department": rng.choice(DEPTS_C),
            "value_gbp": int(value), "procurement_route": rng.choice(ROUTES)}


for _ in range(600):
    s = rng.choice(OTHERS) + " Ltd"
    contracts.append(contract(rng.choice([s, s.upper(), s.lower()]), rng.uniform(20_000, 400_000)))
for _ in range(14):  # biggest SINGLE spelling, but not the biggest supplier (decoy)
    contracts.append(contract("Brownfield Consulting Ltd", rng.uniform(520_000, 680_000)))
for spelling in ("Northgate Digital Ltd", "NORTHGATE DIGITAL LTD", "northgate digital ltd"):  # real winner, split by case
    for _ in range(6):
        contracts.append(contract(spelling, rng.uniform(480_000, 620_000)))
rng.shuffle(contracts)
write("pubsec-contracts", contracts)
raw, norm = collections.Counter(), collections.Counter()
for c in contracts:
    raw[c["supplier"]] += c["value_gbp"]
    norm[c["supplier"].lower()] += c["value_gbp"]
(rn, rv), (r2n, r2v) = raw.most_common(2)
(nn, nv), (n2n, n2v) = norm.most_common(2)
assert rn == "Brownfield Consulting Ltd" and nn == "northgate digital ltd", (rn, nn)
assert nv > n2v * 1.1 and rv > r2v * 1.05, (nv, n2v, rv, r2v)
answers["E6"] = "Northgate Digital Ltd"

# ------------------------------------------------------------------ keys
order = [f"E{i}" for i in range(1, 7)]
code = "".join(str(answers[q])[0].upper() for q in order)
json.dump({"answers": {q: answers[q] for q in order}, "expert_code": code},
          open(os.path.join(HERE, "answer_key_expert.json"), "w"), indent=2)

TOOLS = {"E1": "Discover (KQL)", "E2": "Discover (investigation)", "E3": "Maps", "E4": "Lens (formula)",
         "E5": "Elastic AI Agent", "E6": "ES|QL (TO_LOWER, short)"}
SOLUTIONS = {
    "E1": 'Discover, pubsec-auth. KQL:  event.outcome : "success" and not source.geo.country_iso_code : "GB"   -> one document, read user.name',
    "E2": 'Discover, pubsec-endpoint. KQL:  host.name : "MINISTRY-LT-07" and event.action : "scheduled_task_created"   -> expand the document, read process.command_line (name follows /tn)',
    "E3": 'Maps: add Documents layer on pubsec-potholes, filter severity : "catastrophic", Tooltip fields add nickname, click the northernmost dot (Scotland) and read nickname',
    "E4": 'Lens, pubsec-gritters: Vertical axis = Formula  sum(salt_tonnes) / sum(km_gritted) * 100 ; Horizontal axis = Top values of depot ; tallest bar',
    "E5": f'Two questions to the AI agent. (1) Which department has the slowest average resolved_in_mins for P1 tickets? -> {slowest_dept}. (2) In that department, what is the summary of the P1 ticket with the longest resolved_in_mins? -> "{E5_TICKET["summary"]}" ({E5_TICKET["ticket"]}, {E5_TICKET["resolved_in_mins"]} mins). Check: FROM pubsec-servicedesk | WHERE priority == "P1" AND dept == "{slowest_dept}" | SORT resolved_in_mins DESC | LIMIT 1 | KEEP ticket, resolved_in_mins, summary',
    "E6": 'FROM pubsec-contracts | EVAL name = TO_LOWER(supplier) | STATS total = SUM(value_gbp) BY name | SORT total DESC | LIMIT 1   (gap: TO_LOWER)',
}
TRAPS = {
    "E1": "Forgetting `event.outcome : success`; failed logins come from many countries.",
    "E2": "Needs the host from Q1 and the right event.action (click the field in the sidebar to see values).",
    "E3": "Tooltip fields are empty by default: add `nickname` in layer settings. Decoys sit elsewhere in the UK.",
    "E4": "Formula needs sum / sum (not the average of a ratio) and a x100 so the bars differ visibly.",
    "E5": "Part 2 needs part 1's answer. The agent may average all tickets, not only P1 (that gives HMRC), or pick the longest ticket across all departments.",
    "E6": "Without lower-casing, Brownfield Consulting Ltd looks biggest. Answer is the full supplier name (any capitalisation).",
}
md = ["# EXPERT ROUND answer key (SDR ONLY)\n", "| # | Tool | Answer | Trap |", "|---|---|---|---|"]
md += [f"| {q} | {TOOLS[q]} | **{answers[q]}** | {TRAPS[q]} |" for q in order]
md += ["", f"## Expert code: `{code}`", "",
       "First character of each answer, E1 to E6, uppercase. A matching code means all six are right.", "",
       "## Worked solutions", ""]
md += [f"**{q} ({TOOLS[q]})**\n\n```\n{SOLUTIONS[q]}\n```\n" for q in order]
open(os.path.join(HERE, "SDR_expert_answer_key.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print(json.dumps({"answers": {q: answers[q] for q in order}, "expert_code": code}, indent=2))
