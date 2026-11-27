"""待审队列：已打分、未被判定 interesting/reject 的论文，按相关性降序。"""
from models.paper import Paper


def get_review_queue(store, limit: int = 50) -> list[Paper]:
    return store.review_queue(limit)
