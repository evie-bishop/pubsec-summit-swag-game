# EXPERT ROUND answer key (SDR ONLY)

| # | Tool | Answer | Trap |
|---|---|---|---|
| E1 | Discover (KQL) | **m.holloway** | Forgetting `event.outcome : success`; failed logins come from many countries. |
| E2 | Discover (investigation) | **WhitehallUpdater** | Needs the host from Q1 and the right event.action (click the field in the sidebar to see values). |
| E3 | Maps | **Sandra** | Tooltip fields are empty by default: add `nickname` in layer settings. Decoys sit elsewhere in the UK. |
| E4 | Lens (formula) | **Hilltop Depot** | Formula needs sum / sum (not the average of a ratio) and a x100 so the bars differ visibly. |
| E5 | Elastic AI Agent | **Biscuit tin inventory failed** | Part 2 needs part 1's answer. The agent may average all tickets, not only P1 (that gives HMRC), or pick the longest ticket across all departments. |
| E6 | ES|QL (TO_LOWER, short) | **Northgate Digital Ltd** | Without lower-casing, Brownfield Consulting Ltd looks biggest. Answer is the full supplier name (any capitalisation). |

## Expert code: `MWSHBN`

First character of each answer, E1 to E6, uppercase. A matching code means all six are right.

## Worked solutions

**E1 (Discover (KQL))**

```
Discover, pubsec-auth. KQL:  event.outcome : "success" and not source.geo.country_iso_code : "GB"   -> one document, read user.name
```

**E2 (Discover (investigation))**

```
Discover, pubsec-endpoint. KQL:  host.name : "MINISTRY-LT-07" and event.action : "scheduled_task_created"   -> expand the document, read process.command_line (name follows /tn)
```

**E3 (Maps)**

```
Maps: add Documents layer on pubsec-potholes, filter severity : "catastrophic", Tooltip fields add nickname, click the northernmost dot (Scotland) and read nickname
```

**E4 (Lens (formula))**

```
Lens, pubsec-gritters: Vertical axis = Formula  sum(salt_tonnes) / sum(km_gritted) * 100 ; Horizontal axis = Top values of depot ; tallest bar
```

**E5 (Elastic AI Agent)**

```
Two questions to the AI agent. (1) Which department has the slowest average resolved_in_mins for P1 tickets? -> DVLA. (2) In that department, what is the summary of the P1 ticket with the longest resolved_in_mins? -> "Biscuit tin inventory failed" (TICKET-1359, 91 mins). Check: FROM pubsec-servicedesk | WHERE priority == "P1" AND dept == "DVLA" | SORT resolved_in_mins DESC | LIMIT 1 | KEEP ticket, resolved_in_mins, summary
```

**E6 (ES|QL (TO_LOWER, short))**

```
FROM pubsec-contracts | EVAL name = TO_LOWER(supplier) | STATS total = SUM(value_gbp) BY name | SORT total DESC | LIMIT 1   (gap: TO_LOWER)
```

