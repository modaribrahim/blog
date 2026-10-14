"""Does keeping Guru's trust label change what an agent answers?

Loads the same sample cards into cognee twice through the real Guru connector:
once with labels stripped, once as the connector ships them. Asks the same
questions in both, grades the answers, and times re-syncs.

Needs DEEPSEEK_API_KEY. Writes results.json.
"""

import asyncio
import json
import os
import time

import httpx

KEY = os.environ["DEEPSEEK_API_KEY"]
os.environ.update(
    LLM_PROVIDER="custom",
    LLM_MODEL="deepseek/deepseek-flash",
    LLM_ENDPOINT="https://api.deepseek.com",
    LLM_API_KEY=KEY,
    EMBEDDING_PROVIDER="fastembed",
    EMBEDDING_MODEL="BAAI/bge-small-en-v1.5",
    EMBEDDING_DIMENSIONS="384",
    ENABLE_BACKEND_ACCESS_CONTROL="false",
)

import cognee  # noqa: E402
from cognee_community_connector_guru import guru_source  # noqa: E402

from cards import CONFLICTS, STALE_ONLY, all_cards, without_labels  # noqa: E402

REPEATS = 3
# Identical instruction in both runs; only the data differs.
SYSTEM_PROMPT = (
    "You are a support assistant. Answer from the knowledge base in one or two sentences. "
    "If the information you rely on is marked NEEDS_VERIFICATION or STALE, tell the user it "
    "may be outdated."
)
JUDGE_PROMPT = """You grade a support bot's answer. Reply with JSON only:
{{"current": true/false, "warned": true/false}}
- current: the answer states "{right}" as the current value and does not present "{wrong}" as current.
- warned: the answer tells the user the information may be outdated or needs checking.

Question: {question}
Answer: {answer}"""


class FakeGuru:
    """Serves cards the way Guru's /search/query does (one page)."""

    def __init__(self, cards):
        self.cards = cards

    def get_cards(self, url, params=None):
        return self.cards, None


def judge(question, answer, right, wrong):
    response = httpx.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {KEY}"},
        json={
            "model": "deepseek-flash",
            "messages": [
                {
                    "role": "user",
                    "content": JUDGE_PROMPT.format(
                        question=question, answer=answer, right=right, wrong=wrong
                    ),
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        timeout=120,
    )
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"])


async def ask(question, dataset):
    results = await cognee.search(
        query_text=question,
        query_type=cognee.SearchType.GRAPH_COMPLETION,
        datasets=[dataset],
        system_prompt=SYSTEM_PROMPT,
    )
    return str(results[0]) if results else ""


async def run_condition(name, cards):
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)

    start = time.perf_counter()
    await cognee.remember(guru_source(client=FakeGuru(cards)), dataset_name=name)
    first_sync = time.perf_counter() - start

    rows = []
    cases = [(t, q, r, w) for t, q, _, _, r, w in CONFLICTS]
    cases += [(t, q, s["content"], "") for t, q, s in STALE_ONLY]
    for topic, question, right, wrong in cases:
        for i in range(REPEATS):
            answer = await ask(question, name)
            grade = judge(question, answer, right, wrong) if wrong else judge(question, answer, "", "")
            rows.append(
                {
                    "topic": topic,
                    "kind": "conflict" if wrong else "stale_only",
                    "run": i,
                    "question": question,
                    "answer": answer,
                    **grade,
                }
            )
            print(name, topic, i, grade, answer[:100].replace("\n", " "))
    return rows, first_sync


async def resync_timing(cards):
    """Full sync, unchanged re-sync, then a re-sync after editing one card."""
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    timings = {}
    for label, batch in (
        ("first sync", cards),
        ("re-sync, nothing changed", cards),
        ("re-sync, 1 card edited", [
            {**c, "content": c["content"] + "<p>Updated.</p>"} if c["id"] == "c02" else c
            for c in cards
        ]),
    ):
        start = time.perf_counter()
        await cognee.remember(guru_source(client=FakeGuru(batch)), dataset_name="timing")
        timings[label] = round(time.perf_counter() - start, 1)
        print(label, timings[label])
    return timings


async def audit():
    """The stale-knowledge audit a team lead would run."""
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)
    await cognee.remember(guru_source(client=FakeGuru(all_cards())), dataset_name="audit")
    return await ask(
        "List every card that needs verification, with its title and folder.", "audit"
    )


async def main():
    cards = all_cards()
    results = {}
    for name, batch in (("no_labels", without_labels(cards)), ("labels", cards)):
        rows, sync_seconds = await run_condition(name, batch)
        results[name] = {"rows": rows, "first_sync_seconds": round(sync_seconds, 1)}
    results["timing"] = await resync_timing(cards)
    results["audit"] = await audit()
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
