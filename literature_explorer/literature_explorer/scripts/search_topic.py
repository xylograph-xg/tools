#!/usr/bin/env python3
"""搜索一个研究主题，产出 Top N 候选论文。

用法:
    python scripts/search_topic.py "OLED triplet exciton" [--limit 30] [--db path] [--no-second-wave]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from discovery.loop import run_discovery_cycle
from storage.sqlite import Store


def main():
    parser = argparse.ArgumentParser(description="按主题搜索候选论文")
    parser.add_argument("topic", help="研究主题，如 'OLED triplet exciton'")
    parser.add_argument("--limit", type=int, default=config.CANDIDATE_TOP_N, help="展示数量")
    parser.add_argument("--db", default=None, help="SQLite 路径（默认 data/literature.db）")
    parser.add_argument("--no-second-wave", action="store_true", help="跳过术语反哺的第二波搜索")
    args = parser.parse_args()

    with Store(args.db) as store:
        ranked, scores = run_discovery_cycle(
            store, args.topic, top_n=args.limit, second_wave=not args.no_second_wave
        )
        print(f"\n主题: {args.topic}")
        print(f"候选 {len(ranked)} 篇 / 库中共 {store.count_papers()} 篇\n")
        for i, paper in enumerate(ranked, 1):
            score = scores.get(paper.paper_id, 0.0)
            year = paper.year or "?"
            citations = paper.citation_count if paper.citation_count is not None else "?"
            print(f"[{i:2d}] {score:.3f} | {year} | cited {citations} | {paper.title}")
            if paper.venue:
                print(f"      {paper.venue}")
            print(f"      {paper.paper_id}")
        print("\n下一步: python scripts/review_candidates.py")


if __name__ == "__main__":
    main()
