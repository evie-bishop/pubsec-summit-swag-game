#!/usr/bin/env python3
"""Generate the static, fictional UK public-sector datasets for the Elastic swag game.

Deterministic (fixed seed): re-running always produces identical data and answers.
Outputs (next to this script):
  data/<index>.ndjson       bulk-ready files (action line + doc line)
  answer_key.json           computed answers + the 10-character delegate code
  SDR_answer_key.md         printable key for the SDRs (DO NOT show to players)
"""
import json, math, random, collections, datetime as dt, os

rng = random.Random(2026)
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


answers = {}

# ---------------------------------------------------------------- potholes
COUNCILS = {
    "Puddlesbury": (52.63, 1.30), "Mudchester": (53.48, -2.24),
    "Grittleton": (53.80, -1.55), "Lower Splashing": (50.82, -0.14),
    "Much Rutting": (50.72, -3.53), "Upper Wobble": (55.95, -3.19),
    "Crumbleford": (52.20, 0.12), "Potts End": (54.60, -5.93),
    "Bumpington": (51.62, -3.94), "Little Craterton": (54.98, -1.62),
}
NICK = ["Kevin", "Brenda", "Colin", "Doris", "Gary", "Sharon", "Trevor", "Maureen",
        "Barry", "Pam", "Derek", "Janice", "Keith", "Nigel", "Sandra"]
DESC = ["Swallowed a wheelie bin", "Ate a wing mirror", "Large enough to bathe in",
        "Filled with suspicious water", "Cyclist lost a shoe here", "Has its own ecosystem",
        "Echoes when shouted into", "Recurring problem since 2019", "Resident has named it",
        "Edges crumbling"]
potholes = []


def pothole(council, sev, ts, lat, lon):
    return {"@timestamp": iso(ts), "council": council, "severity": sev,
            "location": {"lat": round(lat, 5), "lon": round(lon, 5)},
            "nickname": rng.choice(NICK), "status": rng.choice(["open", "open", "scheduled", "repaired"]),
            "description": rng.choice(DESC), "width_cm": rng.randint(8, 90)}


names = list(COUNCILS)
w = [rng.uniform(0.8, 1.3) for _ in names]
for _ in range(3000):
    c = rng.choices(names, w)[0]
    lat, lon = COUNCILS[c]
    potholes.append(pothole(c, rng.choices(["low", "medium", "high"], [.5, .33, .17])[0], rand_ts(),
                            lat + rng.gauss(0, .08), lon + rng.gauss(0, .1)))
# Q6: a cluster of catastrophic craters around Manchester
for _ in range(150):
    potholes.append(pothole("Mudchester", "catastrophic", rand_ts(),
                            53.4808 + rng.gauss(0, .03), -2.2426 + rng.gauss(0, .04)))
# decoy catastrophic potholes elsewhere
for c in ["Bumpington", "Upper Wobble", "Much Rutting", "Potts End", "Crumbleford", "Grittleton"]:
    lat, lon = COUNCILS[c]
    potholes.append(pothole(c, "catastrophic", rand_ts(), lat + rng.gauss(0, .08), lon + rng.gauss(0, .1)))
# Q9: "Storm Brenda" spike on 9 Feb 2026
SPIKE_DAY = dt.datetime(2026, 2, 9, 12, tzinfo=dt.timezone.utc)
for _ in range(400):
    c = rng.choices(names, w)[0]
    lat, lon = COUNCILS[c]
    potholes.append(pothole(c, rng.choices(["medium", "high"], [.6, .4])[0],
                            SPIKE_DAY + dt.timedelta(minutes=rng.randint(-300, 300)),
                            lat + rng.gauss(0, .08), lon + rng.gauss(0, .1)))
rng.shuffle(potholes)
write("pubsec-potholes", potholes)

cnt = collections.Counter(p["council"] for p in potholes)
answers["Q2"] = cnt["Much Rutting"]
daily = collections.Counter(p["@timestamp"][:10] for p in potholes)
top_day, top_n = daily.most_common(1)[0]
assert top_day == "2026-02-09" and top_n > 2 * daily.most_common(2)[1][1]
answers["Q9"] = int(top_day[-2:])
answers["Q6"] = "Manchester"

# ---------------------------------------------------------------- canteen
DEPTS = ["Treasury", "Cabinet Office", "Home Office", "DEFRA", "DfE", "DWP", "MoJ",
         "FCDO", "DHSC", "HMRC", "MoD", "DfT"]
BISC = {"Jammie Dodger": 1.6, "Digestive": 1.15, "Hobnob": 1.1, "Rich Tea": 1.0, "Custard Cream": 1.0,
        "Bourbon": .8, "Ginger Nut": .7, "Jaffa Cake": .9}
canteen = []
for _ in range(2500):
    canteen.append({"@timestamp": iso(rand_ts()), "department": rng.choice(DEPTS),
                    "biscuit": rng.choices(list(BISC), list(BISC.values()))[0],
                    "packets": rng.randint(1, 12), "meeting_type": rng.choice(
                        ["stand-up", "spending review", "away day", "all-hands", "crisis meeting"])})
write("pubsec-canteen", canteen)
tot = collections.Counter()
for c in canteen:
    tot[c["biscuit"]] += c["packets"]
(b1, n1), (b2, n2) = tot.most_common(2)
assert n1 > n2 * 1.08, (b1, n1, b2, n2)
answers["Q3"] = b1

# ---------------------------------------------------------------- planning
STREETS = ["Acacia Avenue", "Church Lane", "High Street", "Mill Road", "Station Road", "The Green",
           "Orchard Close", "Victoria Terrace", "Elm Grove", "Windmill Way"]
BASE = ["Erection of single-storey rear extension", "Loft conversion with rear dormer",
        "Replacement of UPVC windows", "Change of use from shop to cafe", "Installation of solar panels",
        "Demolition of garage and erection of annexe", "Garden room for home working",
        "Removal of chimney stack", "New front porch", "Conversion of barn to dwelling",
        "Erection of boundary fence", "Block paving to front garden"]
SURN = ["Smith", "Patel", "Jones", "Williams", "Taylor", "Brown", "Khan", "Davies", "Evans", "Wilson",
        "Thomas", "Roberts", "Johnson", "Walker", "Wright", "Robinson", "Thompson", "Hughes"]
planning = []


def app(desc, surname, first=None):
    return {"@timestamp": iso(rand_ts()), "reference": f"PL/{rng.randint(2026000, 2026999)}/{rng.randint(10, 99)}",
            "council": rng.choice(names), "address": f"{rng.randint(1, 120)} {rng.choice(STREETS)}",
            "description": desc, "applicant_name": f"{first or rng.choice(['A.', 'J.', 'M.', 'S.', 'R.', 'K.'])} {surname}",
            "decision": rng.choice(["approved", "approved", "refused", "pending"])}


for _ in range(1500):
    planning.append(app(rng.choice(BASE), rng.choice(SURN)))
DRAGON = ["Installation of dragon-proof roof tiles", "Construction of dragon stable at rear of property",
          "Retrospective permission for dragon landing pad on flat roof",
          "Fireproof extension to accommodate resident dragon",
          "Reinforced chimney to withstand dragon activity", "Dragon flap in front door",
          "Singe-resistant hedge, dragon height", "Dragon hatchery in garden shed",
          "Erection of dragon observation tower", "Moving dragon-feeding station to side elevation",
          "Fire-retardant gazebo suitable for dragon barbecue", "Dragon-friendly driveway widening",
          "Appeal against refusal of dragon kennel"]
for d in DRAGON:
    planning.append(app(d, rng.choice(SURN)))
planning.append(app("Construction of defensive moat around semi-detached property", "Pendragon", "Arthur"))
rng.shuffle(planning)
write("pubsec-planning", planning)
answers["Q4"] = sum("dragon" in p["description"].lower() for p in planning)
assert not any("moat" in p["description"].lower() for p in planning if p["applicant_name"] != "Arthur Pendragon")
assert sum("pendragon" in p["applicant_name"].lower() for p in planning) == 1
answers["Q10"] = "Pendragon"

# ---------------------------------------------------------------- gritters
GRITTERS = ["Gritzilla", "Grit Eastwood", "Gritney Spears", "The Gritfather", "Gritty Potter",
            "Salty McSaltface", "Frosty Gritman", "Mr Grittle", "Gritchcock", "Spice Grits",
            "Gritman Begins", "Flurry Weather", "Brr-ian Cox", "Lord of the Grits", "Gritley Scott",
            "Sleet Beatles", "Thaw Pole", "Grit Expectations", "Ice Ice Baby", "Slush Puppy"]
gw = {g: rng.uniform(.7, 1.2) for g in GRITTERS}
gw["Gritzilla"] = 1.6
gritters = []
for _ in range(1500):
    g = rng.choices(list(gw), list(gw.values()))[0]
    gritters.append({"@timestamp": iso(rand_ts()), "gritter": g,
                     "depot": rng.choice(["North Depot", "South Depot", "Hilltop Depot", "Coastal Depot"]),
                     "km_gritted": round(rng.uniform(5, 90), 1), "salt_tonnes": round(rng.uniform(.5, 9), 2)})
write("pubsec-gritters", gritters)
gc = collections.Counter(g["gritter"] for g in gritters).most_common(2)
assert gc[0][1] > gc[1][1] * 1.2, gc
answers["Q5"] = gc[0][0]

# ---------------------------------------------------------------- portal
SERVICES = ["Renew Bin Licence", "Book Driving Test", "Pay Council Tax", "Report a Pothole",
            "Apply for Passport", "Blue Badge", "Library Renewals", "Register to Vote"]
COUNTRIES = ["GB", "GB", "GB", "GB", "IE", "US", "FR", "DE", "IN"]
portal = []
for _ in range(20000):
    portal.append({"@timestamp": iso(rand_ts()), "service": rng.choice(SERVICES),
                   "http": {"response": {"status_code": rng.choices([200, 301, 404, 403], [90, 4, 4, 2])[0]}},
                   "response_time_ms": int(min(5000, rng.lognormvariate(5.5, .6))),
                   "client": {"country": rng.choice(COUNTRIES)}})
idx = rng.sample(range(len(portal)), 300)
five_weights = {s: 1 for s in SERVICES}
five_weights["Book Driving Test"] = 4
for i in idx:
    s = rng.choices(list(five_weights), list(five_weights.values()))[0]
    portal[i]["service"] = s
    portal[i]["http"]["response"]["status_code"] = rng.choice([500, 502, 503])
portal[rng.randrange(len(portal))]["response_time_ms"] = 42042
write("pubsec-portal", portal)
fc = collections.Counter(p["service"] for p in portal if p["http"]["response"]["status_code"] >= 500)
assert sum(fc.values()) == 300 and fc.most_common(1)[0][1] > fc.most_common(2)[1][1] * 1.4, fc
answers["Q7"] = fc.most_common(1)[0][0]
answers["Q8"] = max(p["response_time_ms"] for p in portal)

# ---------------------------------------------------------------- endpoint (Q1: Attack Discovery)
# ECS-style endpoint telemetry. Benign noise plus ONE planted, entirely fictional attack chain on
# MINISTRY-LT-07. Detection rules (see setup_cluster.py) fire only on the chain; Attack Discovery
# then stitches the alerts into a single story naming the host.
HOSTS = [f"{d}-{k}-{n:02d}" for d in ("MINISTRY", "COUNCIL", "DEPOT") for k in ("LT", "PC") for n in range(1, 6)]
HOSTS = [h for h in HOSTS if h != "MINISTRY-LT-07"] + ["MINISTRY-LT-06", "MINISTRY-LT-08"]
USERS = ["j.smith", "p.patel", "m.jones", "s.khan", "d.evans", "r.wilson", "k.thomas", "l.walker"]
BENIGN = [
    ("process", "process_started", "chrome.exe", "explorer.exe", "chrome.exe --profile-directory=Default"),
    ("process", "process_started", "outlook.exe", "explorer.exe", "outlook.exe"),
    ("process", "process_started", "teams.exe", "explorer.exe", "teams.exe"),
    ("process", "process_started", "powershell.exe", "explorer.exe", "powershell.exe -File C:\\IT\\inventory.ps1"),
    ("file", "file_opened", "WINWORD.EXE", "explorer.exe", "WINWORD.EXE minutes.docx"),
    ("file", "file_opened", "EXCEL.EXE", "explorer.exe", "EXCEL.EXE budget.xlsx"),
    ("authentication", "logon_success", "winlogon.exe", "wininit.exe", "winlogon.exe"),
]
endpoint = []


def ev(ts, host, user, cat, action, proc, parent, cmd, **extra):
    d = {"@timestamp": iso(ts), "host": {"name": host}, "user": {"name": user},
         "event": {"category": cat, "action": action, "kind": "event"},
         "process": {"name": proc, "parent": {"name": parent}, "command_line": cmd},
         "message": f"{action} by {user} on {host}"}
    for k, v in extra.items():
        d[k] = v
    return d


for _ in range(5000):
    cat, act, proc, parent, cmd = rng.choice(BENIGN)
    endpoint.append(ev(rand_ts(), rng.choice(HOSTS), rng.choice(USERS), cat, act, proc, parent, cmd))
for _ in range(120):  # benign big transfers (backups), well under the exfil threshold
    endpoint.append(ev(rand_ts(), rng.choice(HOSTS), "svc.backup", "network", "network_connection",
                       "backup.exe", "services.exe", "backup.exe --nightly",
                       network={"bytes": rng.randint(10_000_000, 400_000_000)},
                       destination={"domain": "backup.council.example", "ip": "10.20.0.5"}))
T0 = dt.datetime(2026, 3, 3, 9, 14, tzinfo=dt.timezone.utc)
V, U = "MINISTRY-LT-07", "a.gresham"
chain = [
    (0, ev(T0, V, U, "file", "attachment_opened", "WINWORD.EXE", "OUTLOOK.EXE",
           "WINWORD.EXE Invoice_Q1_Overdue.docm", file={"name": "Invoice_Q1_Overdue.docm", "extension": "docm"})),
    (2, ev(T0, V, U, "process", "process_started", "powershell.exe", "WINWORD.EXE",
           "powershell.exe -nop -w hidden -enc VGhpcyBpcyBhIGZpY3Rpb25hbCBnYW1lIHBheWxvYWQ=")),
    (9, ev(T0, V, U, "process", "scheduled_task_created", "schtasks.exe", "powershell.exe",
           "schtasks.exe /create /tn WhitehallUpdater /tr C:\\Users\\Public\\upd.exe /sc hourly")),
    (21, ev(T0, V, U, "process", "lsass_access", "upd.exe", "schtasks.exe", "upd.exe --read-memory")),
    (47, ev(T0, V, U, "network", "network_connection", "upd.exe", "schtasks.exe", "upd.exe --upload",
            network={"bytes": 4_200_000_000},
            destination={"domain": "totally-legit-backup.example", "ip": "203.0.113.50"})),
]
for mins, d in chain:
    d["@timestamp"] = iso(T0 + dt.timedelta(minutes=mins))
    endpoint.append(d)
rng.shuffle(endpoint)
write("pubsec-endpoint", endpoint)
answers["Q1"] = V


order = [f"Q{i}" for i in range(1, 11)]
code = "".join(str(answers[q])[0].upper() for q in order)
key = {"answers": {q: answers[q] for q in order}, "delegate_code": code}
json.dump(key, open(os.path.join(HERE, "answer_key.json"), "w"), indent=2)

QTEXT = {
    "Q1": "Attack Discovery: infected host name", "Q2": "Discover: KQL, count Much Rutting potholes",
    "Q3": "ES|QL: top biscuit by packets", "Q4": "Discover: free-text search, count 'dragon' applications",
    "Q5": "Lens: gritter with the most runs", "Q6": "Maps: catastrophic pothole cluster, nearest city",
    "Q7": "Discover: top service for 5xx errors", "Q8": "ES|QL: slowest response (ms)",
    "Q9": "Discover histogram: day-of-month of the spike", "Q10": "AI: ask the assistant who applied for the moat (surname)"}
md = ["# SDR answer key (KEEP OFF THE TABLE)\n", "| # | Feature | Answer |", "|---|---|---|"]
md += [f"| {q} | {QTEXT[q]} | **{answers[q]}** |" for q in order]
md += ["", f"## Delegate code: `{code}`", "",
       "First character of each answer, Q1 to Q10, uppercase. If the delegate's code matches, all ten are right. "
       "If it doesn't, ask them to re-read the answers they wrote down and send them back."]
open(os.path.join(HERE, "SDR_answer_key.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print(json.dumps(key, indent=2))
