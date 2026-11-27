"""人工反馈：interesting / reject / later（later 会回到待审队列）。"""
DECISIONS = ("interesting", "reject", "later")


def record_feedback(store, paper_id: str, decision: str, note: str = ""):
    if decision not in DECISIONS:
        raise ValueError(f"decision 必须是 {DECISIONS} 之一，收到: {decision}")
    store.record_feedback(paper_id, decision, note)


def interesting_papers(store):
    return store.interesting_papers()
