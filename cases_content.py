"""Content for the 10 Kibana Cases. Answers are NOT in here."""
from urllib.parse import quote

TIME = "(time:(from:'2026-01-01T00:00:00.000Z',to:'2026-04-01T00:00:00.000Z'))"


def _enc(s):
    return quote(s, safe="")


def attack_discovery(kb):
    """Security app URL with an absolute range that covers when the discovery was generated (20 Oct 2026)."""
    tr = "(from:'2026-10-20T00:00:00.000Z',kind:absolute,to:'2027-12-31T23:59:59.999Z')"
    t = f"(global:(linkTo:!(timeline),timerange:{tr}),timeline:(linkTo:!(global),timerange:{tr}))"
    return f"{kb}/app/security/attack_discovery?timerange={_enc(t)}"


def discover(kb, dv, kql=""):
    a = f"(dataSource:(dataViewId:{dv},type:dataView),query:(language:kuery,query:'{kql}'))"
    return f"{kb}/app/discover#/?_g={_enc(TIME)}&_a={_enc(a)}"


def esql(kb, query):
    a = f"(dataSource:(type:esql),query:(esql:'{query}'))"
    return f"{kb}/app/discover#/?_g={_enc(TIME)}&_a={_enc(a)}"


FOOT = ("\n\n---\n*Write your answer on your answer sheet. **Do not** click Save, Edit or anything that sounds "
        "like it changes things; you're read-only anyway. Stuck? Wave at an Elastic person.*")


def build_cases(kb):
    """Return list of dicts: title, description, comments[]. Order = Q1..Q10."""
    c = []

    c.append(dict(
        title="Q1 | Who Clicked the Invoice?",
        description=(
            "## Welcome, Agent\n\nOn 3 March a civil servant opened an 'overdue invoice' email. Our security "
            "tools raised several alerts, and an AI has already stitched them together into one story using "
            "**Attack Discovery**.\n\n"
            f"**Go to:** [Security > Attack Discovery]({attack_discovery(kb)})\n\n"
            "1. Open the attack discovery that has been generated for you. If the list looks empty, change the "
            "date picker at the top of the page to **Last 1 year** (the alerts date from October 2026). "
            "Don't generate anything new, just view the existing result.\n"
            "2. Read the title and summary. It names the **laptop (host)** that was compromised.\n\n"
            "**Answer format:** the host name exactly as shown (letters, digits and dashes)." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q2 | The Pothole Census",
        description=(
            "## Operation Crater Count\n\nCouncils across the land have been logging potholes, and several have "
            "been given names by furious residents. We need an exact count for the council of **Much Rutting**.\n\n"
            f"**Go to:** [Discover: Potholes]({discover(kb, 'pubsec-potholes')})\n\n"
            "1. In the search bar at the top, type `council : \"Much Rutting\"` and press Enter.\n"
            "2. Look at the top-left of the results: it shows the number of documents (hits).\n\n"
            "**Answer format:** a number." + FOOT),
        comments=[]))

    q3 = "FROM pubsec-canteen | STATS packets = SUM(packets) BY biscuit | SORT packets DESC | LIMIT 3"
    c.append(dict(
        title="Q3 | The Great Biscuit Audit",
        description=(
            "## Whitehall's Biscuit Barrel\n\nA whistleblower claims one biscuit is eaten far more than any other "
            "in government meetings. Time to find out which.\n\n"
            f"**Go to:** [Discover with ES|QL (query pre-loaded)]({esql(kb, q3)})\n\n"
            "The query is already filled in. Press **Run** (or Ctrl+Enter) if it hasn't run. It adds up packets "
            "per biscuit and sorts the biggest first.\n\n"
            f"```\n{q3}\n```\n\n"
            "**Answer format:** the name of the biscuit in first place." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q4 | Planning Permission for Dragons",
        description=(
            "## Here Be Dragons\n\nThe planning department has noticed some... unusual applications. "
            "Search the free text of every application to find out how many involve a **dragon**.\n\n"
            f"**Go to:** [Discover: Planning applications]({discover(kb, 'pubsec-planning')})\n\n"
            "1. Type `dragon` in the search bar and press Enter.\n"
            "2. Read the document count at the top left.\n\n"
            "**Answer format:** a number." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q5 | Gritter Idol",
        description=(
            "## The Gritters Have Names\n\nOur gritting fleet has a strong sense of humour. We need to crown "
            "the hardest-working gritter: the one with the most gritting **runs** (one document = one run).\n\n"
            f"**Go to:** [Lens (new visualisation)]({kb}/app/lens#/)\n\n"
            "1. Make sure the data view (top left) is **pubsec-gritters**.\n"
            "2. Drag the field **gritter** from the left sidebar onto the middle of the canvas.\n"
            "3. You get a bar chart: the tallest bar is the winner. If names are cut off, hover the bar.\n"
            "4. Don't save. Just read.\n\n"
            "**Answer format:** the gritter's name, exactly as shown." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q6 | Crater Cluster",
        description=(
            "## Something Terrible Happened Somewhere\n\nMost potholes are annoying. A few are **catastrophic**. "
            "One part of the country has a suspicious cluster of them. Where?\n\n"
            f"**Go to:** [Maps]({kb}/app/maps/map)\n\n"
            "1. Click **Add layer** > **Documents**, and choose the data view **pubsec-potholes**. "
            "Click **Add and continue**.\n"
            "2. In the search bar at the top of the map, type `severity : \"catastrophic\"` and press Enter.\n"
            "3. Zoom out to see the UK. Find the big blob of points.\n"
            "4. Don't save. Just look.\n\n"
            "**Answer format:** the nearest **city** to the cluster (e.g. 'Leeds')." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q7 | Website Meltdown",
        description=(
            "## The Citizen Portal Is On Fire\n\nSomewhere in the online services, things are going wrong. "
            "Server errors are **HTTP 500 and above**. Which service is breaking the most?\n\n"
            f"**Go to:** [Discover: Portal logs]({discover(kb, 'pubsec-portal', 'http.response.status_code >= 500')})\n\n"
            "The filter is pre-filled (check the search bar shows `http.response.status_code >= 500`; "
            "if not, type it in).\n"
            "1. In the left sidebar find the field **service** and click its name.\n"
            "2. A popup shows the **top values** with percentages. Read the biggest one.\n\n"
            "**Answer format:** the service name, exactly as shown." + FOOT),
        comments=[]))

    q8 = "FROM pubsec-portal | STATS slowest_ms = MAX(response_time_ms)"
    c.append(dict(
        title="Q8 | The Slowest Click in Britain",
        description=(
            "## Please Hold, Your Call Is Important To Us\n\nOne poor citizen waited a *very* long time for a "
            "page to load. How long, in milliseconds, was the slowest response?\n\n"
            f"**Go to:** [Discover with ES|QL (query pre-loaded)]({esql(kb, q8)})\n\n"
            f"```\n{q8}\n```\n\n"
            "Press **Run** if needed and read the single number in the result.\n\n"
            "**Answer format:** a number (no commas)." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q9 | Storm Brenda",
        description=(
            "## Date With Destiny\n\nStorm Brenda hit and pothole reports shot up on a single day. "
            "Find the day of the spike.\n\n"
            f"**Go to:** [Discover: Potholes]({discover(kb, 'pubsec-potholes')})\n\n"
            "1. Above the results is a bar chart. Click the small interval dropdown above the chart and choose "
            "**Day**.\n"
            "2. Find the one enormous bar. Hover over it to see its date.\n\n"
            "**Answer format:** the **day of the month** only (e.g. 'the 21st' becomes 21)." + FOOT),
        comments=[]))

    c.append(dict(
        title="Q10 | The Castle Conspiracy",
        description=(
            "## Final Case: Ask the Robot\n\nSomeone has applied to build a **moat** around a semi-detached "
            "house. Don't search for it yourself. Make the **AI Assistant** do the work.\n\n"
            "1. Open the AI Assistant (the sparkle / assistant button at the top right of Kibana).\n"
            "2. Paste this in and send it:\n\n"
            "```\nSearch the pubsec-planning index for any planning application that mentions a moat. "
            "What is the applicant_name?\n```\n\n"
            "3. If the robot gets confused, ask it again more simply. Be patient, it can take a few seconds.\n"
            "4. *Backup plan:* [Discover]("
            f"{discover(kb, 'pubsec-planning')}) and search `moat`.\n\n"
            "**Answer format:** the applicant's **surname**.\n\n"
            "Then take your ten answers back to the Elastic team on the swag table. Well done, Agent!" + FOOT),
        comments=[]))
    return c
