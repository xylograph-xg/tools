#!/usr/bin/env python3
"""逐篇审核候选论文：interesting / reject / later。

用法:
    python scripts/review_candidates.py [--limit 50] [--db path]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from screening.feedback import record_feedback
from screening.queue import get_review_queue
from storage.sqlite import Store

_ACTIONS = {"i": "interesting", "r": "reject", "l": "later"}


def _show(index, total, paper, score):
    print("=" * 72)
    print(f"({index}/{total}) score={score:.3f} | {paper.year or '?'} | cited {paper.citation_count if paper.citation_count is not None else '?'}")
    print(paper.title)
    if paper.venue:
        print(f"venue: {paper.venue}")
    if paper.authors:
        print("authors: " + ", ".join(paper.authors[:5]) + (" et al." if len(paper.authors) > 5 else ""))
    if paper.abstract:
        abstract = paper.abstract if len(paper.abstract) <= 600 else paper.abstract[:600] + "..."
        print(f"abstract: {abstract}")
    print(f"id: {paper.paper_id}")


def main():
    parser = argparse.ArgumentParser(description="人工审核候选论文")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--db", default=None)
    args = parser.parse_args()

    with Store(args.db) as store:
        queue = get_review_queue(store, limit=args.limit)
        if not queue:
            print("待审队列为空。先运行: python scripts/search_topic.py \"<topic>\"")
            return
        print(f"待审 {len(queue)} 篇。[i]nteresting [r]eject [l]ater [s]kip [q]uit")
        reviewed = 0
        for index, paper in enumerate(queue, 1):
            _show(index, len(queue), paper, store.score_for(paper.paper_id) or 0.0)
            while True:
                try:
                    choice = input("> ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    choice = "q"
                if choice in _ACTIONS:
                    note = ""
                    if choice == "i":
                        try:
                            note = input("  备注（可空）: ").strip()
                        except (EOFError, KeyboardInterrupt):
                            note = ""
                    record_feedback(store, paper.paper_id, _ACTIONS[choice], note)
                    reviewed += 1
                    break
                if choice in ("s", ""):
                    break
                if choice == "q":
                    print(f"已审核 {reviewed} 篇，退出。")
                    return
                print("输入 i/r/l/s/q")
        print(f"完成，本轮审核 {reviewed} 篇。下一步: python scripts/expand_interesting.py")


if __name__ == "__main__":
    main()
