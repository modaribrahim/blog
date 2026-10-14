"""Turn results.json into the two charts used in the blog post."""

import json

import matplotlib.pyplot as plt

results = json.load(open("results.json"))


def rate(name, kind, field):
    rows = [r for r in results[name]["rows"] if r["kind"] == kind]
    return 100 * sum(r[field] for r in rows) / len(rows)


metrics = [
    ("Gave the current answer\n(old and new card conflict)", "conflict", "current"),
    ("Warned it may be outdated\n(only an old card exists)", "stale_only", "warned"),
]
colors = {"no_labels": "#b0b0b0", "labels": "#2f6fdf"}
names = {"no_labels": "Labels dropped", "labels": "Labels kept (this connector)"}

fig, ax = plt.subplots(figsize=(7, 4.4))
width = 0.36
for i, name in enumerate(("no_labels", "labels")):
    values = [rate(name, kind, field) for _, kind, field in metrics]
    xs = [x + (i - 0.5) * width for x in range(len(metrics))]
    bars = ax.bar(xs, values, width, label=names[name], color=colors[name])
    ax.bar_label(bars, fmt="%.0f%%", padding=3)
ax.set_xticks(range(len(metrics)), [m[0] for m in metrics])
ax.set_ylim(0, 110)
ax.set_ylabel("% of answers")
ax.set_title("Same bot, same cards — only the trust label changes")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
fig.tight_layout()
fig.savefig("accuracy.png", dpi=200)

timing = results["timing"]
fig, ax = plt.subplots(figsize=(7, 3))
bars = ax.barh(list(timing), list(timing.values()), color="#2f6fdf")
ax.bar_label(bars, fmt="%.1fs", padding=3)
ax.invert_yaxis()
ax.set_xlabel("seconds")
ax.set_title("Re-sync only re-processes what changed")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("resync.png", dpi=200)
print("saved accuracy.png, resync.png")
