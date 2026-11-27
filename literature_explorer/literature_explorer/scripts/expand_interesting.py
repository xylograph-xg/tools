#!/usr/bin/env python3
"""对所有 interesting 论文做引文扩展（references + citations），生成下一批候选。

只对未扩展过的论文抓取（citation_fetches scope_key 去重），可重复运行。

用法:
    python scripts/expand_interesting.py [--limit 30] [--db path]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from discovery.citation_expand import expand_from_paper
from ranking import relevance
from screening.feedback import interesting_papers
from storage.sqlite import Store


def main():
    parser = argparse.ArgumentParser(description="从 interesting 论文扩展新候选")
    parser.add_argument("--limit", type=int, default=config.CANDIDATE_TOP_N, help="展示数量")
    parser.add_argument("--db", default=None)
    args = parser.parse_args()

    with Store(args.db) as store:
        seeds = interesting_papers(store)
        if not seeds:
            print("还没有 interesting 论文。先运行: python scripts/review_candidates.py")
            return
        latest = store.latest_run()
        topic = latest[1] if latest else ""
        run_id = store.create_run(f"expand:{topic}" if topic else "expand")

        all_found: dict[str, object] = {}
        for seed in seeds:
            found = expand_from_paper(store, seed.paper_id, run_id)
            print(f"{seed.title[:60]} -> +{len(found)} 篇")
            for paper in found:
                all_found.setdefault(paper.paper_id, paper)
        store.finish_run(run_id, "done")

        if not all_found:
            print("没有新候选（种子可能都已扩展过）。")
            return

        scores = relevance.score_papers(store, topic, list(all_found.values()))
        ranked = relevance.rank(list(all_found.values()), scores)
        print(f"\n新候选 {len(ranked)} 篇（topic: {topic}）\n")
        for i, paper in enumerate(ranked[: args.limit], 1):
            score = scores.get(paper.paper_id, 0.0)
            provenance = "; ".join(store.provenance_for(paper.paper_id))
            print(f"[{i:2d}] {score:.3f} | {paper.year or '?'} | {paper.title}")
            print(f"      {provenance}")
        print("\n下一步: python scripts/review_candidates.py")


if __name__ == "__main__":
    main()
