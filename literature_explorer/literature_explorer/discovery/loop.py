"""Discovery loop：topic → 搜索 → 术语反哺第二波 → 打分排序 → Top N。

第一版单轮产出候选即完成验收；多轮自动循环（边际收益停止）放到
review/expand 人工闭环稳定之后。
"""
import config
from discovery import query_expand, search
from models.paper import Paper
from ranking import relevance


def run_discovery_cycle(store, topic: str, top_n: int = config.CANDIDATE_TOP_N,
                        second_wave: bool = True) -> tuple[list[Paper], dict[str, float]]:
    run_id = store.create_run(topic)
    try:
        all_papers: dict[str, Paper] = {}
        for query in query_expand.initial_queries(topic):
            for paper in search.search_papers(store, query, run_id, round_no=0):
                all_papers[paper.paper_id] = paper

        scores = relevance.score_papers(store, topic, list(all_papers.values()))

        if second_wave:
            for query in query_expand.expanded_queries(store, topic, current_papers=list(all_papers.values()), scores=scores):
                for paper in search.search_papers(store, query, run_id, round_no=1):
                    if paper.paper_id not in all_papers:
                        all_papers[paper.paper_id] = paper
            scores = relevance.score_papers(store, topic, list(all_papers.values()))

        store.finish_run(run_id, "done")
    except Exception:
        store.finish_run(run_id, "failed")
        raise

    ranked = relevance.rank(list(all_papers.values()), scores)
    return ranked[:top_n], scores
