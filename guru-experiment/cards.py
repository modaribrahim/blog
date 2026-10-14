"""Sample Guru workspace for a made-up SaaS company ("Northwind Cloud").

Eight topics have an old card (NEEDS_VERIFICATION, wrong value) and a newer
card (TRUSTED, right value). Four topics only have an old card. Card shape
follows Guru's /search/query response.
"""

COLLECTION = {"name": "Support"}


def card(cid, title, html, state, folder, reason=None, verified="2026-09-01T10:00:00.000+0000"):
    c = {
        "id": cid,
        "slug": f"{cid}/{title.replace(' ', '-')}",
        "preferredPhrase": title,
        "content": html,
        "verificationState": state,
        "lastVerified": verified,
        "collection": COLLECTION,
        "boards": [{"title": folder}],
    }
    if reason:
        c["verificationReason"] = reason
    return c


STALE = "NEEDS_VERIFICATION"
OLD = "2024-03-01T10:00:00.000+0000"

# (topic, question, stale card, trusted card, right value, wrong value)
CONFLICTS = [
    (
        "refund",
        "How many days do customers have to ask for a refund?",
        card("c01", "Refund policy", "<p>Customers can request a full refund within <b>30 days</b> of purchase.</p>", STALE, "Billing", "EXPIRED", OLD),
        card("c02", "Refund policy 2026", "<p>Since January 2026, refunds are only possible within <b>14 days</b> of purchase.</p>", "TRUSTED", "Billing"),
        "14 days",
        "30 days",
    ),
    (
        "price",
        "How much does the Pro plan cost per month?",
        card("c03", "Pro plan pricing", "<p>The Pro plan costs <b>$29 per month</b>.</p>", STALE, "Billing", "EXPIRED", OLD),
        card("c04", "Pricing update", "<p>Pro plan price is now <b>$39 per month</b> for all new and existing customers.</p>", "TRUSTED", "Billing"),
        "$39",
        "$29",
    ),
    (
        "hours",
        "When is the support team available?",
        card("c05", "Support hours", "<p>Our support team is available <b>24/7</b>.</p>", STALE, "Support", "EXPIRED", OLD),
        card("c06", "Support hours (current)", "<p>Support is available <b>Monday to Friday, 8am to 8pm UTC</b>.</p>", "TRUSTED", "Support"),
        "Monday to Friday",
        "24/7",
    ),
    (
        "reset",
        "How long is a password reset link valid?",
        card("c07", "Password reset", "<p>Password reset links expire after <b>24 hours</b>.</p>", STALE, "Account", "UPDATE", OLD),
        card("c08", "Password reset security change", "<p>Password reset links now expire after <b>1 hour</b>.</p>", "TRUSTED", "Account"),
        "1 hour",
        "24 hours",
    ),
    (
        "upload",
        "What is the maximum file upload size?",
        card("c09", "Upload limits", "<p>Max upload size is <b>2 GB</b> per file.</p>", STALE, "Product", "EXPIRED", OLD),
        card("c10", "Upload limits 2026", "<p>Files up to <b>5 GB</b> can be uploaded.</p>", "TRUSTED", "Product"),
        "5 GB",
        "2 GB",
    ),
    (
        "retention",
        "How long do we keep data after a customer cancels?",
        card("c11", "Data retention", "<p>After cancellation, data is kept for <b>90 days</b>.</p>", STALE, "Account", "EXPIRED", OLD),
        card("c12", "Data retention policy", "<p>After cancellation, data is deleted after <b>30 days</b>.</p>", "TRUSTED", "Account"),
        "30 days",
        "90 days",
    ),
    (
        "trial",
        "How long is the free trial?",
        card("c13", "Free trial", "<p>New accounts get a <b>7-day</b> free trial.</p>", STALE, "Billing", "EXPIRED", OLD),
        card("c14", "Free trial length", "<p>The free trial lasts <b>21 days</b>.</p>", "TRUSTED", "Billing"),
        "21 days",
        "7 days",
    ),
    (
        "ratelimit",
        "What is the API rate limit?",
        card("c15", "API rate limits", "<p>The API allows <b>100 requests per minute</b>.</p>", STALE, "Developers", "EXPIRED", OLD),
        card("c16", "API rate limits v2", "<p>The API allows <b>600 requests per minute</b> per key.</p>", "TRUSTED", "Developers"),
        "600",
        "100 requests",
    ),
]

# (topic, question, stale card) — no newer card exists.
STALE_ONLY = [
    (
        "sso",
        "Which SSO methods do we support?",
        card("c17", "SSO setup", "<p>We support <b>SAML only</b> for single sign-on.</p>", STALE, "Security", "EXPIRED", OLD),
    ),
    (
        "phone",
        "What is the support phone number?",
        card("c18", "Phone support", "<p>Call support at <b>+1 555 0100</b>.</p>", STALE, "Support", "EXPIRED", OLD),
    ),
    (
        "nonprofit",
        "Do nonprofits get a discount?",
        card("c19", "Nonprofit discount", "<p>Registered nonprofits get <b>50% off</b> any plan.</p>", STALE, "Billing", "EXPIRED", OLD),
    ),
    (
        "region",
        "Where is EU customer data stored?",
        card("c20", "EU data region", "<p>EU customer data is stored in <b>Frankfurt</b>.</p>", STALE, "Security", "EXPIRED", OLD),
    ),
]


def all_cards():
    return [c for _, _, s, t, _, _ in CONFLICTS for c in (s, t)] + [s for _, _, s in STALE_ONLY]


def without_labels(cards):
    """The same cards as a connector that drops Guru's trust signal would see them."""
    drop = {"verificationState", "verificationReason", "lastVerified"}
    return [{k: v for k, v in c.items() if k not in drop} for c in cards]
