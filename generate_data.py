#!/usr/bin/env python3
"""Generate synthetic Salesforce-style CRM data as CSVs for the dbt project.

Entities: accounts, contacts, leads, opportunities, activities, quotas,
marketing_spend. Deterministic (fixed seed) so the dataset is reproducible.

Time span: 2024-01-01 to 2026-09-30. "Today" is assumed to be 2026-10-05,
so open opportunities carry close_dates in the future (2026-10-06 onward).
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUT = Path(__file__).parent / "seeds"
OUT.mkdir(exist_ok=True)

START = date(2024, 1, 1)
END = date(2026, 9, 30)
TODAY = date(2026, 10, 5)

INDUSTRIES = [
    "Software", "Healthcare", "Financial Services", "Retail", "Manufacturing",
    "Education", "Media", "Logistics", "Hospitality", "Energy",
]
SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
# (min_emp, max_emp, share, median_deal)
SEGMENT_SPECS = {
    "SMB": (5, 200, 0.50, 28_000),
    "Mid-Market": (201, 1000, 0.32, 130_000),
    "Enterprise": (1001, 20000, 0.18, 480_000),
}
REPS = [
    "Ava Chen", "Liam Park", "Sofia Reyes", "Noah Kim",
    "Maya Patel", "Ethan Wright", "Olivia Zhang", "Lucas Meyer",
]
STAGES = [
    "Prospecting", "Qualification", "Needs Analysis",
    "Proposal", "Closed Won", "Closed Lost",
]
STAGE_PROB = {
    "Prospecting": 10, "Qualification": 25, "Needs Analysis": 50,
    "Proposal": 75, "Closed Won": 100, "Closed Lost": 0,
}
# Funnel decay: share of all opportunities landing in each stage
STAGE_DIST = [
    ("Prospecting", 0.16), ("Qualification", 0.15), ("Needs Analysis", 0.14),
    ("Proposal", 0.12), ("Closed Won", 0.18), ("Closed Lost", 0.25),
]
CYCLE_DAYS = {  # (min, max) created -> close, by segment
    "SMB": (25, 75), "Mid-Market": (60, 150), "Enterprise": (120, 280),
}
LEAD_SOURCES = ["Outbound", "Paid Search", "Organic", "Webinar", "Referral", "Partner", "Event"]
SOURCE_WEIGHTS = [0.30, 0.20, 0.15, 0.12, 0.10, 0.08, 0.05]
SOURCE_CONV = {  # lead -> opportunity conversion rate by source
    "Referral": 0.40, "Webinar": 0.32, "Partner": 0.30, "Organic": 0.28,
    "Event": 0.25, "Paid Search": 0.20, "Outbound": 0.15,
}
ACTIVITY_TYPES = ["Call", "Email", "Meeting", "Demo"]
TITLES = ["VP Sales", "Director of Ops", "CFO", "Head of IT", "Procurement Manager",
          "Sales Manager", "COO", "Marketing Director"]


def rand_date(a: date, b: date) -> date:
    return a + timedelta(days=random.randint(0, (b - a).days))


def pick_stage() -> str:
    r = random.random()
    cum = 0.0
    for stage, w in STAGE_DIST:
        cum += w
        if r < cum:
            return stage
    return STAGE_DIST[-1][0]


def pick_segment() -> str:
    r = random.random()
    cum = 0.0
    for seg in SEGMENTS:
        cum += SEGMENT_SPECS[seg][2]
        if r < cum:
            return seg
    return SEGMENTS[-1]


# ---------------------------------------------------------------- accounts
accounts = []
for i in range(1, 201):
    segment = pick_segment()
    lo, hi, _, _ = SEGMENT_SPECS[segment]
    accounts.append({
        "account_id": f"ACC-{i:04d}",
        "account_name": f"{fake.company()}",
        "industry": random.choice(INDUSTRIES),
        "segment": segment,
        "region": random.choice(["West", "East", "Central", "South"]),
        "employee_count": random.randint(lo, hi),
        "created_date": rand_date(START, END).isoformat(),
    })

# ---------------------------------------------------------------- contacts
contacts, cid = [], 1
for acc in accounts:
    for _ in range(random.randint(1, 4)):
        fn, ln = fake.first_name(), fake.last_name()
        contacts.append({
            "contact_id": f"CON-{cid:05d}",
            "account_id": acc["account_id"],
            "first_name": fn, "last_name": ln,
            "email": f"{fn.lower()}.{ln.lower()}@{fake.domain_name()}",
            "title": random.choice(TITLES),
            "created_date": rand_date(START, END).isoformat(),
        })
        cid += 1

# ---------------------------------------------------------------- leads
leads = []
for i in range(1, 3001):
    source = random.choices(LEAD_SOURCES, weights=SOURCE_WEIGHTS)[0]
    created = rand_date(START, END)
    converted = random.random() < SOURCE_CONV[source]
    leads.append({
        "lead_id": f"LEAD-{i:05d}",
        "company": fake.company(),
        "first_name": fake.first_name(), "last_name": fake.last_name(),
        "email": fake.email(),
        "source": source,
        "status": "Converted" if converted else random.choice(
            ["New", "Working", "Nurturing", "New", "Working", "Disqualified"]),
        "created_date": created.isoformat(),
        "owner": random.choice(REPS),
        "_converted": converted, "_created": created,
    })

# ---------------------------------------------------------------- opportunities
# ~750 come from converted leads (real lineage), rest are rep-sourced.
converted_leads = [l for l in leads if l["_converted"]]
random.shuffle(converted_leads)

opportunities = []
oid = 1


def make_opp(account, contact_id, created, source, rep, converted_lead_id=None):
    global oid
    segment = account["segment"]
    stage = pick_stage()
    median = SEGMENT_SPECS[segment][3]
    amount = int(random.lognormvariate(
        __import__("math").log(median), 0.9))
    amount = max(3_000, min(amount, 3_000_000))
    lo, hi = CYCLE_DAYS[segment]
    if stage in ("Closed Won", "Closed Lost"):
        closed = created + timedelta(days=random.randint(lo, hi))
        close_date = min(closed, END)
    else:
        # Open pipeline: forecast close in the future (after TODAY)
        close_date = TODAY + timedelta(days=random.randint(5, 150))
    opp = {
        "opportunity_id": f"OPP-{oid:05d}",
        "account_id": account["account_id"],
        "primary_contact_id": contact_id,
        "name": f"{account['account_name']} - {random.choice(['Platform', 'Enterprise', 'Growth', 'Scale'])} Deal",
        "stage": stage,
        "amount": amount,
        "probability": STAGE_PROB[stage],
        "close_date": close_date.isoformat(),
        "created_date": created.isoformat(),
        "owner": rep,
        "lead_source": source,
        "segment": segment,
        "converted_lead_id": converted_lead_id or "",
    }
    oid += 1
    return opp


# Opportunities sourced from converted leads
contacts_by_account = {}
for c in contacts:
    contacts_by_account.setdefault(c["account_id"], []).append(c["contact_id"])

n_from_leads = min(750, len(converted_leads))
for lead in converted_leads[:n_from_leads]:
    account = random.choice(accounts)
    cids = contacts_by_account.get(account["account_id"], [""])
    created = max(lead["_created"], rand_date(START, END))
    opportunities.append(make_opp(
        account, random.choice(cids), created, lead["source"],
        lead["owner"], converted_lead_id=lead["lead_id"]))

# Rep-sourced opportunities (fill up to 1500)
while len(opportunities) < 1500:
    account = random.choice(accounts)
    cids = contacts_by_account.get(account["account_id"], [""])
    opportunities.append(make_opp(
        account, random.choice(cids), rand_date(START, END),
        random.choice(["Outbound", "Outbound", "Referral", "Partner"]),
        random.choice(REPS)))

# Link converted leads back to their opportunity ids
lead_to_opp = {}
for opp in opportunities:
    if opp["converted_lead_id"]:
        lead_to_opp[opp["converted_lead_id"]] = opp["opportunity_id"]
for lead in leads:
    lead["converted_opportunity_id"] = lead_to_opp.get(lead["lead_id"], "")
    lead["converted_date"] = (
        (lead["_created"] + timedelta(days=random.randint(3, 21))).isoformat()
        if lead["_converted"] else "")
    del lead["_converted"], lead["_created"]

# ---------------------------------------------------------------- activities
activities = []
aid = 1
for opp in opportunities[:1200]:  # activities on a subset to keep volume sane
    for _ in range(random.randint(1, 6)):
        created = date.fromisoformat(opp["created_date"])
        close = date.fromisoformat(opp["close_date"])
        if close < created:
            close = created
        activities.append({
            "activity_id": f"ACT-{aid:06d}",
            "what_id": opp["opportunity_id"],
            "what_type": "Opportunity",
            "activity_type": random.choice(ACTIVITY_TYPES),
            "activity_date": rand_date(created, close).isoformat(),
            "owner": opp["owner"],
        })
        aid += 1
for lead in random.sample(leads, 800):
    activities.append({
        "activity_id": f"ACT-{aid:06d}",
        "what_id": lead["lead_id"],
        "what_type": "Lead",
        "activity_type": random.choice(["Call", "Email", "Email", "Meeting"]),
        "activity_date": lead["created_date"],
        "owner": lead["owner"],
    })
    aid += 1

# ---------------------------------------------------------------- quotas & spend
quotas = []
base = {"SMB": 900_000, "Mid-Market": 1_800_000, "Enterprise": 2_500_000}
quarters = []
y, q = 2024, 1
while (y, q) <= (2027, 1):
    quarters.append(f"{y}-Q{q}")
    q += 1
    if q > 4:
        y, q = y + 1, 1
for idx, quarter in enumerate(quarters):
    growth = 1 + 0.04 * idx  # ~4% quarterly quota growth
    for seg in SEGMENTS:
        quotas.append({
            "segment": seg,
            "quarter": quarter,
            "quota_amount": int(base[seg] * growth * random.uniform(0.97, 1.03)),
        })

spend_base = {"Outbound": 450_000, "Paid Search": 800_000, "Organic": 120_000,
              "Webinar": 250_000, "Referral": 80_000, "Partner": 300_000, "Event": 550_000}
marketing_spend = []
for quarter in quarters:
    for src in LEAD_SOURCES:
        marketing_spend.append({
            "source": src,
            "quarter": quarter,
            "spend_amount": int(spend_base[src] * random.uniform(0.9, 1.1)),
        })


def write(name, rows):
    with open(OUT / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


write("raw_accounts", accounts)
write("raw_contacts", contacts)
write("raw_leads", leads)
write("raw_opportunities", opportunities)
write("raw_activities", activities)
write("raw_quotas", quotas)
write("raw_marketing_spend", marketing_spend)
print("done.")
