# Case Files: the Elastic swag game (PubSec Summit 2026)

Ten short "case files" in Kibana, fictional UK public-sector data, no Elastic knowledge needed. Delegates answer ten questions on a laptop, bring back their answers plus a 10-character code, and get swag.

> **Keep this repo private.** `generate_data.py` contains the planted answers.

## Repo contents

| File | Purpose |
|---|---|
| `generate_data.py` | Builds 6 static, seeded datasets into `data/` plus `answer_key.json` and `SDR_answer_key.md` (both git-ignored) |
| `cases_content.py` | The 10 case write-ups, with deep links into Discover / ES\|QL / Security / Lens / Maps |
| `setup_cluster.py` | Loads data, creates data views, creates detection rules and the Cases |
| `clean_conversations.py` | Deletes players' AI chats so delegates never see each other's conversations |

## The 10 cases

| # | Title | Kibana feature | Player does |
|---|---|---|---|
| 1 | Who Clicked the Invoice? | Attack Discovery | Read the pre-generated discovery, name the infected host |
| 2 | The Pothole Census | Discover (KQL) | Filter by council, read hit count |
| 3 | The Great Biscuit Audit | ES\|QL | Run a pre-loaded query, read top row |
| 4 | Planning Permission for Dragons | Discover (full text) | Search `dragon`, read hit count |
| 5 | Gritter Idol | Lens | Drag one field, read the tallest bar |
| 6 | Crater Cluster | Maps | Add a layer, spot the cluster, name the city |
| 7 | Website Meltdown | Discover (field top values) | Click a field, read top value |
| 8 | The Slowest Click in Britain | ES\|QL | Run a pre-loaded query, read a number |
| 9 | Storm Brenda | Discover (histogram) | Find the tallest bar, read its day |
| 10 | Ask the Robot | Elastic AI Agent (Agent Builder) | Paste a prompt, read the applicant surname |

Indices: `pubsec-endpoint`, `pubsec-potholes`, `pubsec-canteen`, `pubsec-planning`, `pubsec-gritters`, `pubsec-portal`. All timestamps fall in Jan-Mar 2026 (endpoint attack chain on 3 Mar).

**Delegate code:** first character of each answer, Q1 to Q10, uppercase. It is printed in `SDR_answer_key.md` after you run `generate_data.py`.

## Requirements

- Elastic Cloud Hosted deployment, Stack 9.x, with an LLM connector (Elastic managed connector works) for Attack Discovery and Agent Builder.
- **Kibana instance of at least 4 GB RAM.** At 1 GB it hits high native memory pressure under Security + Attack Discovery and returns "resource unavailable" / "Kibana server is not ready yet".
- Python 3 and `pip install requests`.

## Setup

1. Create an admin API key (Stack Management > API keys). Copy the **Encoded** value.
2. Set environment variables (PowerShell shown; use `export` on macOS/Linux):

   ```powershell
   $env:KIBANA_URL = "https://<deployment>.kb.<region>.aws.cloud.es.io"
   $env:ES_URL     = "https://<deployment>.es.<region>.aws.cloud.es.io"   # NOT the .ingest. endpoint
   $env:API_KEY    = "<encoded key>"
   ```

3. `python generate_data.py` (creates `data/`, `answer_key.json`, `SDR_answer_key.md`).
4. `python setup_cluster.py` runs data, views, settings, rules and cases.
   - On Elastic Cloud the Kibana settings API is blocked, so the "settings" step prints a warning. Set it by hand: **Stack Management > Advanced settings > Time filter defaults** to `{"from":"2026-01-01T00:00:00.000Z","to":"2026-04-01T00:00:00.000Z"}`.
5. **Attack Discovery (Q1).** Wait ~10 minutes for 5-6 alerts in Security > Alerts. In Security > Attack discovery set the range to Last 24 hours, pick the connector and **Generate** once. Confirm the result names `MINISTRY-LT-07`. Then freeze the alerts: `python setup_cluster.py --only disable-rules`.
6. Create the player role and users (below), then play all ten yourself.

`setup_cluster.py` options:

| Command | Effect |
|---|---|
| `--only data / views / settings / rules / cases` | Run one step |
| `--only data --index pubsec-potholes` | Reload a single index |
| `--only cases --recreate-cases` | Delete and recreate all game cases (tag `pubsec-game`) |
| `--update-case Q1` | Patch only that case's description, leaving other cases untouched |
| `--only disable-rules` | Disable the detection rules after alerts exist |
| `--owner cases\|securitySolution\|observability` | Case owner (default `cases`: view under Stack Management > Cases) |

## Player role and users

Role `swag_player`:

- **Cluster privilege:** `monitor_inference` (lets the AI agent list models).
- **Index privileges** (all `read` + `view_index_metadata`): `pubsec-*`, `.alerts-security.alerts-*`, `.internal.alerts-security.alerts-*`, `.lists-*`, `.items-*`, `.siem-signals-*`, `.adhoc.alerts-security.attack.discovery.alerts-*`, `.alerts-security.attack.discovery.alerts-*`.
- **Kibana privileges (Default space), Read:** Discover, Maps, Visualize Library, Cases, Security (incl. Attack discovery and AI features), Agent Builder if listed. Everything else None.
- One-off, as admin, so the Security app is usable by players:
  `POST /api/detection_engine/index` and `POST /api/lists/index`.

Player accounts (one per laptop, so chats are not shared). The ES API call works without the Kibana UI:

```powershell
$h = @{Authorization="ApiKey $env:API_KEY"}
1..8 | ForEach-Object {
  $b = @{password="<password>"; roles=@("swag_player"); full_name="Player $_"} | ConvertTo-Json
  Invoke-RestMethod "$env:ES_URL/_security/user/player$_" -Method Post -Headers $h -Body $b -ContentType "application/json"
}
```

Log each laptop in once beforehand and label it.

## AI chats (Q10) are saved on the cluster

Agent Builder conversations persist server-side and are private per user. Run the sweeper on your own laptop for the whole event:

```powershell
python clean_conversations.py --kibana-url $env:KIBANA_URL --users player1,player2,player3 --password "<password>"
```

It logs in with a browser-style session (plain Basic auth sees an empty list), and deletes each player's chats once idle for 2 minutes (`--min-age`). Use `--once --min-age 0` to wipe everything before doors open. Add `--debug` to see what it finds. Delete your own admin/SSO test chats by hand. SDRs should also click **New conversation** between delegates.

If you want a strictly write-free cluster, change Q10 to the Discover search (already in the case as a backup).

## Event kit

**Player answer sheet (print):**

```
CASE FILES: answer sheet           Name: ______________

 1. Infected laptop (host name) .......... ______________
 2. Much Rutting potholes ................ ______________
 3. Most-eaten biscuit ................... ______________
 4. Planning apps mentioning dragons ..... ______________
 5. Hardest-working gritter .............. ______________
 6. City nearest the crater cluster ...... ______________
 7. Service with the most server errors .. ______________
 8. Slowest response (ms) ................ ______________
 9. Day of the month of Storm Brenda ..... ______________
10. Applicant surname (the moat) ......... ______________

DELEGATE CODE: FIRST LETTER or DIGIT of each answer, 1 to 10, in order:
[ _ ][ _ ][ _ ][ _ ][ _ ][ _ ][ _ ][ _ ][ _ ][ _ ]
```

**SDR script:** "Fancy some swag? Grab a laptop and solve ten short case files in Kibana. No Elastic experience needed: each case tells you where to click. Bring us your answers and your ten-character code and the swag is yours. About 10-15 minutes."

Login card: Kibana URL and "open **Stack Management > Cases** and start with Q1" (the laptops are pre-logged-in).

Verification: compare the delegate's code to `SDR_answer_key.md`. Match = swag. No match = send them back to re-check, without saying which answer is wrong. Keep the key off the table.

## Known gotchas

- Cases created with owner `cases` only appear under **Stack Management > Cases**, not Security > Cases.
- Attack Discovery results are stored with their generation time, so the Q1 link uses an absolute date range from 20 Oct 2026. If you regenerate on another date, edit `attack_discovery()` in `cases_content.py` and run `--update-case Q1`.
- Q9 needs the Discover chart interval set to **Day** (the case says so).
- Players can still share answers. The 10-character code only proves all ten are right.
- Delete the setup API key after the event, and delete AI conversations.
