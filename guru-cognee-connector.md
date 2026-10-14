---
title: "My AI support bot now knows when our docs are outdated"
---

So here's the thing.. Every team has a wiki, but half of it is old. And personally based on what I've seen, it happens all the time, so we need a solution for that. In our case, Guru tries to fix that. Every card has a trust label: **Trusted**, **Stale**, or **Needs verification**. An expert re-checks cards on a schedule.

But when you plug a wiki into an AI agent, that label is lost. The bot reads an outdated card and answers like it's fact....

For Mergetober I built a Guru connector for [Cognee](https://github.com/topoteretes/cognee) that keeps the label.

## The use case: a support bot that doesn't lie with confidence

I like to think of a support team with 300 Guru cards: refund rules, pricing, setup guides.

A customer asks: "Can I get a refund after 30 days?"

- The refund card is **Trusted** → the bot answers.
- The refund card **Needs verification** (policy changed, nobody updated it) → the bot still answers, but says: "This info may be outdated. Please confirm with the team."

Same bot, same data, but yeah, it just knows which answers to trust.

## I tested it

I didn't want to just claim it, so I ran an experiment.

- 20 sample Guru cards for a made-up company. 8 topics have an old card (wrong, needs verification) and a new one (right, trusted). 4 topics only have an old card.
- Loaded them into Cognee twice through the connector: once with the trust labels dropped, once with them kept.
- Asked the same 12 questions, 3 times each. Same bot, same prompt. Model: DeepSeek V4.1 Flash.

![results](accuracy.png)

When old and new cards disagree, the bot mostly gets it right anyway (92% → 100%).

The big one: when **only an old card exists**, the bot without labels warned **0 times out of 12**. It just repeated old info as fact. With labels: **12 out of 12**.

Real answers to "Do nonprofits get a discount?":

> **Labels dropped:** Yes — registered nonprofits get 50% off any plan.

> **Labels kept:** Yes — registered nonprofits get 50% off any plan. Note that this entry is marked NEEDS_VERIFICATION (EXPIRED, last verified 2024-03-01), so the discount may be outdated.

Bonus: I asked "list every card that needs verification". It found 11 of the 12. That's a free cleanup list for the team.

Syncing again is cheap too, because only changed cards get processed:

![re-sync](resync.png)

The whole experiment cost about $0.30 in API calls. Code and raw results: [guru-experiment](https://github.com/modaribrahim/blog/tree/main/guru-experiment).

## What the connector does

I will mention here and try to be brief:

- Pulls Guru cards into Cognee memory.
- Puts the trust label in each card's text, so the agent sees it.
- Keeps collection and folder names, so context isn't lost.
- Card deleted in Guru? Gone from memory on the next sync.
- Only changed cards are processed again. Saves LLM cost.
- If Guru's API fails mid-sync, it stops. Nothing gets wrongly deleted.

## How to use it

The best way to explain it actually is by coding it:

```python
import cognee
from cognee_community_connector_guru import guru_source

source = guru_source(email="you@company.com", token="...")
await cognee.remember(source, dataset_name="guru")

answer = await cognee.search(
    query_text="Can I get a refund after 30 days?",
    datasets=["guru"],
)
```

Only want trusted cards? `guru_source(verification_state="trusted")`.
One folder? `guru_source(folder_id="...")`.

## Testing

The connector has 49 tests. I ran them on a fresh Ubuntu 24.04 VM with Python 3.11. The Guru API is mocked, so anyone can run them without an account...

## Links

- PR: https://github.com/topoteretes/cognee-community/pull/238
- Issue: https://github.com/topoteretes/cognee/issues/4721
- Mergetober: https://www.wemakedevs.org/hackathons/mergetober
