#!/usr/bin/env python3
"""Sweep AI chat conversations for the player accounts so delegates never see each other's chats.

AI chats are private to the user who made them, so with one shared login everyone sees everyone's
history. Fix: one login per laptop (player1..playerN) plus this sweeper, which deletes each player's
conversations once they have been idle for --min-age seconds.

It logs in with a session cookie like the browser does (plain Basic auth has no user profile, so the
chat list comes back empty), then sweeps these chat stores:
  - Agent Builder:           /api/agent_builder/conversations
  - Security AI Assistant:   /api/security_ai_assistant/current_user/conversations

Usage (leave running for the event):
  python clean_conversations.py --kibana-url https://<kibana> --users player,player1,player2 --password <pw>
Flags: --once (single pass), --min-age 0 (delete everything), --debug (show what it sees),
       --provider NAME (login provider, default cloud-basic)
"""
import argparse, datetime as dt, time
import requests

DEBUG = False
SESSIONS = {}
PROVIDER = "cloud-basic"  # Elastic Cloud's username/password login provider


def session_for(kb, user, pw, force=False):
    """Log in like the browser does so chats are tied to the user's profile (Basic auth sees none)."""
    if not force and user in SESSIONS:
        return SESSIONS[user]
    s = requests.Session()
    s.headers.update({"kbn-xsrf": "true", "x-elastic-internal-origin": "kibana", "elastic-api-version": "2023-10-31"})
    r = s.post(f"{kb}/internal/security/login", timeout=30, json={
        "providerType": "basic", "providerName": PROVIDER, "currentURL": f"{kb}/",
        "params": {"username": user, "password": pw}})
    if r.status_code >= 400:
        raise RuntimeError(f"login failed {r.status_code}: {r.text[:200]}")
    SESSIONS[user] = s
    return s


def parse_ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def items_of(body):
    if isinstance(body, list):
        return body
    for k in ("results", "data", "conversations", "items"):
        if isinstance(body.get(k), list):
            return body[k]
    return []


def ts_of(c):
    for k in ("updated_at", "updatedAt", "created_at", "createdAt", "timestamp"):
        if c.get(k):
            return parse_ts(c[k])
    return None


def sweep_store(kb, user, pw, min_age, label, list_url, params, delete_url):
    sess = session_for(kb, user, pw)
    r = sess.get(f"{kb}{list_url}", params=params, timeout=30)
    if r.status_code == 401:  # session expired
        sess = session_for(kb, user, pw, force=True)
        r = sess.get(f"{kb}{list_url}", params=params, timeout=30)
    if r.status_code >= 400:
        if DEBUG or r.status_code not in (404,):
            print(f"[{user}] {label}: list failed {r.status_code}: {r.text[:200]}")
        return
    items = items_of(r.json())
    if DEBUG:
        print(f"[{user}] {label}: HTTP {r.status_code}, conversations found: {len(items)}")
        if items:
            print(f"[{user}] {label}: first item: {str(items[0])[:300]}")
    now = dt.datetime.now(dt.timezone.utc)
    deleted = 0
    for c in items:
        ts = ts_of(c)
        if ts and ts.tzinfo and (now - ts).total_seconds() < min_age:
            continue  # still in use
        d = sess.delete(f"{kb}{delete_url.format(id=c['id'])}", timeout=30)
        if d.status_code < 400:
            deleted += 1
        else:
            print(f"[{user}] {label}: delete failed {d.status_code}: {d.text[:200]}")
    if deleted:
        print(f"[{user}] {label}: deleted {deleted} conversation(s)")


def sweep(kb, user, pw, min_age):
    sweep_store(kb, user, pw, min_age, "agent-builder",
                "/api/agent_builder/conversations", {},
                "/api/agent_builder/conversations/{id}")
    sweep_store(kb, user, pw, min_age, "agent-builder (elastic-ai-agent)",
                "/api/agent_builder/conversations", {"agent_id": "elastic-ai-agent"},
                "/api/agent_builder/conversations/{id}")
    sweep_store(kb, user, pw, min_age, "security-ai-assistant",
                "/api/security_ai_assistant/current_user/conversations/_find",
                {"page": 1, "per_page": 100},
                "/api/security_ai_assistant/current_user/conversations/{id}")


def main():
    global DEBUG, PROVIDER
    ap = argparse.ArgumentParser()
    ap.add_argument("--kibana-url", required=True)
    ap.add_argument("--users", required=True, help="comma-separated, e.g. player1,player2")
    ap.add_argument("--password", required=True)
    ap.add_argument("--min-age", type=int, default=120, help="only delete chats idle this many seconds")
    ap.add_argument("--interval", type=int, default=30)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--provider", default="cloud-basic", help="login provider name (default cloud-basic)")
    ap.add_argument("--debug", action="store_true", help="print what each sweep sees")
    a = ap.parse_args()
    DEBUG = a.debug
    PROVIDER = a.provider
    kb = a.kibana_url.rstrip("/")
    users = [u.strip() for u in a.users.split(",") if u.strip()]
    while True:
        for u in users:
            try:
                sweep(kb, u, a.password, a.min_age)
            except Exception as e:  # keep going through blips (e.g. Kibana restarting)
                print(f"[{u}] error: {e}")
        if a.once:
            break
        time.sleep(a.interval)


if __name__ == "__main__":
    main()
