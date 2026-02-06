"""Quick audit of the full platform data."""
import json
from urllib.request import Request, urlopen


def api(path, data=None, token=None):
    url = f"http://localhost:8000{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method="POST" if data else "GET")
    with urlopen(req) as resp:
        return json.loads(resp.read())

# Handler login
r = api("/api/auth/login", {"email":"handler@intelliplan.se","password":"handler123"})
token = r["token"]

# Detail for req-004 (has pending assignment)
d = api("/api/requests/req-004", token=token)
print(f"=== {d['request']['title']} ===")
print(f"Customer: {d['customer']['company']}")
a = d['assessment']
print(f"Assessment: conf={a['confidence_score']} rating={a['overall_rating']}")
print(f"Risks: {a.get('risks', [])}")
print(f"Recs: {a.get('recommendations', [])}")
print(f"Matching: {len(d['matching_consultants'])}")
for m in d['matching_consultants']:
    print(f"  {m['name']}: {m['match_score']}% match")
print(f"Assignments: {len(d['assignments'])}")
for asgn in d['assignments']:
    cn = asgn['consultant_name']
    st = asgn['status']
    hr = asgn['hourly_rate']
    print(f"  {cn} - status={st} - {hr}SEK/h")
print(f"Timeline: {len(d['timeline'])} events")
print()

# Customer login (anna @ volvo)
r2 = api("/api/auth/login", {"email":"anna.lindstrom@volvo.com","password":"kund123"})
token2 = r2["token"]
reqs = api("/api/requests", token=token2)
print(f"=== CUSTOMER VIEW: {len(reqs)} requests visible ===")
for rq in reqs:
    title = rq['title'][:50]
    status = rq['status']
    print(f"  {title} [{status}]")
print()

# Notifications for handler
notifs = api("/api/notifications", token=token)
unread = sum(1 for n in notifs if not n['is_read'])
print(f"=== NOTIFICATIONS: {len(notifs)} total, {unread} unread ===")
for n in notifs[:5]:
    flag = "[NEW]" if not n['is_read'] else "     "
    msg = n['message'][:60]
    print(f"  {flag} {msg}")
