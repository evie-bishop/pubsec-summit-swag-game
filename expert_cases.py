"""Content for the optional EXPERT ROUND cases (E1-E6). Answers are NOT in here.

Mix of tools: Discover (KQL), Discover (investigation), Maps, Lens (formula), AI agent, ES|QL.
"""
from cases_content import esql, discover, FOOT

BANNER = ("> ## EXPERT ROUND: optional and harder\n"
          "> This is **separate** from the main ten questions and is **not needed** for the swag.\n\n")


def esql_link(kb, q):
    return f"[Open in Discover with ES|QL (skeleton pre-loaded)]({esql(kb, q)})"


def build_expert_cases(kb):
    """Return list of dicts: title, description, comments[], tags[]. Order = intro, E1..E6."""
    c = []
    tags = ["expert"]

    c.append(dict(
        title="EXPERT ROUND | Read me first (optional, harder)",
        tags=tags,
        description=(
            "# EXPERT ROUND\n\n"
            "**This is a separate, harder round.** You only need the first ten questions (Q1 to Q10) for the swag. "
            "Finish those first and hand them in.\n\n"
            "These are harder questions to challenge the more technically inclined.\n\n"
            "**What's different:** you do more of the work yourself. The six questions use six different tools: "
            "Discover search, an investigation in Discover, Maps, a Lens formula, an AI agent question and one short ES|QL query. "
            "Each case gives you hints and, where it helps, a query with a gap (`???`) to fill in.\n\n"
            "**How to answer:** write each answer in the Expert Round box of your answer sheet, then build your "
            "**6-character expert code**: the first letter or digit of each answer, E1 to E6, in order.\n\n"
            "Same rules as before: you're read-only, so nothing you do can break anything. Wave if you're stuck."),
        comments=[]))

    kql1 = 'event.outcome : "success"'
    kql2 = 'host.name : "MINISTRY-LT-07"'
    c.append(dict(
        title="EXPERT E1 | The Impossible Commute",
        tags=tags,
        description=(BANNER +
            "## One account, two countries\n\nStaff log in from Britain. But one account has a **successful** login "
            "from somewhere else, which is a classic sign of a stolen password.\n\n"
            f"**Go to:** [Discover: Authentication logs]({discover(kb, 'pubsec-auth', kql1)})\n\n"
            "The search bar already shows `event.outcome : \"success\"`. Add to it so that it **excludes** logins from "
            "Britain (country code `GB`). The field is `source.geo.country_iso_code`.\n\n"
            "*Hint:* KQL supports `and` and `not`, for example `... and not field : \"value\"`.\n\n"
            "**Answer format:** the username (e.g. `j.smith`)." + FOOT),
        comments=[]))

    c.append(dict(
        title="EXPERT E2 | What Did the Attacker Leave Behind?",
        tags=tags,
        description=(BANNER +
            "## Persistence\n\nRemember the infected laptop from Q1? The attacker made sure they could get back in by "
            "creating a **scheduled task**. What did they call it?\n\n"
            f"**Go to:** [Discover: Endpoint events]({discover(kb, 'pubsec-endpoint', kql2)})\n\n"
            "The search bar already limits results to that laptop. Now find the event where the task was created:\n\n"
            "1. In the left sidebar, click the field **event.action** to see the values that occur.\n"
            "2. Click the **+** next to the one that looks like a scheduled task being created, to add it as a filter.\n"
            "3. Expand the result (little arrow on the left) and read **process.command_line**.\n\n"
            "*Hint:* in a `schtasks /create` command, the task name comes after `/tn`.\n\n"
            "**Answer format:** the task name, exactly as written." + FOOT),
        comments=[]))

    c.append(dict(
        title="EXPERT E3 | The Lonely Crater",
        tags=tags,
        description=(BANNER +
            "## Northernmost catastrophe\n\nMost catastrophic potholes are in the big Manchester cluster, but a few "
            "are scattered around the country. One of them is **further north than all the others**. Residents have "
            "given each pothole a nickname. What is this one called?\n\n"
            f"**Go to:** [Maps]({kb}/app/maps/map)\n\n"
            "1. Click **Add layer** > **Documents**, choose the data view **pubsec-potholes**, then **Add and "
            "continue**.\n"
            "2. In the search bar above the map, type `severity : \"catastrophic\"` and press Enter.\n"
            "3. Open the layer's settings (click the layer name), find **Tooltip fields**, and add **nickname**.\n"
            "4. Zoom out to the UK, find the dot furthest north, and click it to read its tooltip.\n"
            "5. Don't save.\n\n"
            "**Answer format:** the nickname." + FOOT),
        comments=[]))

    c.append(dict(
        title="EXPERT E4 | Thirsty Gritters",
        tags=tags,
        description=(BANNER +
            "## Salt per kilometre\n\nSalt is expensive. Which depot uses the most salt **per 100 km gritted**?\n\n"
            f"**Go to:** [Lens]({kb}/app/lens#/)\n\n"
            "1. Make sure the data view (top left) is **pubsec-gritters**.\n"
            "2. Drag the field **depot** onto the canvas. Lens makes a bar chart.\n"
            "3. Lens only shows the **top 3** depots by default, and there are more. Click the **horizontal axis** "
            "(the depot field in the right-hand panel) and raise **Number of values** to **10**.\n"
            "4. Click the **vertical axis** (the Count field in the right-hand panel) and choose the **Formula** "
            "tab.\n"
            "5. Enter a formula that adds up `salt_tonnes`, divides by the sum of `km_gritted`, then multiplies "
            "by 100. Lens formulas look like `sum(field_a) / sum(field_b)`.\n"
            "6. Read the bars. Hover over them for exact values. Don't save.\n\n"
            "*Hint:* the ×100 is there to make the differences between depots easy to see.\n\n"
            "**Answer format:** the depot name, exactly as shown." + FOOT),
        comments=[]))

    c.append(dict(
        title="EXPERT E5 | Ask the Agent: Slowest Fixers",
        tags=tags,
        description=(BANNER +
            "## The IT service desk (AI agent)\n\nThe IT service desk logs tickets as P1 (most urgent) down to P4. "
            "In this question you will use the agent to find the answer. "
            "**You will need to ask it at least two questions.**\n\n"
            "1. Open the Elastic AI Agent (the sparkle button at the top right of Kibana).\n"
            "2. **Question 1.** Ask it which department is slowest, on average, to resolve its **P1** tickets:\n\n"
            "```\nLook at the pubsec-servicedesk index. Which department has the slowest average resolved_in_mins "
            "for P1 tickets?\n```\n\n"
            "3. **Question 2.** Now ask a follow-up about **that department**. You need to find the **P1 ticket that "
            "took the longest to resolve**, and read out its **summary**. Write this question yourself, using the "
            "department from question 1 and the fields `priority`, `resolved_in_mins` and `summary`.\n"
            "4. **Check its working.** If an answer doesn't mention P1 or the department, ask: *\"Show me the "
            "query you used.\"* and try again. Be patient, it can take a few seconds.\n\n"
            "**Answer format:** the ticket's summary text, exactly as written." + FOOT),
        comments=[]))

    q = ('FROM pubsec-contracts | EVAL name = ???(supplier) | STATS total = SUM(value_gbp) BY name '
         '| SORT total DESC | LIMIT 1')
    c.append(dict(
        title="EXPERT E6 | One Supplier, Three Spellings",
        tags=tags,
        description=(BANNER +
            "## Follow the money (ES|QL)\n\nWho has been paid the most in government contracts? The catch: the same "
            "supplier is typed in different ways (`Acme Ltd`, `ACME LTD`, `acme ltd`), so one company can look like "
            "several, and the biggest-looking name may not be the biggest supplier.\n\n"
            f"**Go to:** {esql_link(kb, q)}\n\n"
            "Replace `???` with the function that turns text into **lower case**, so every spelling becomes the "
            "same name before the totals are added up.\n\n"
            f"```\n{q}\n```\n\n"
            "*Hint:* start typing `TO_` in the query editor and it will suggest functions.\n\n"
            "**Answer format:** the top supplier's full name (any capitalisation, e.g. `acme ltd`)." + FOOT),
        comments=[]))
    return c
