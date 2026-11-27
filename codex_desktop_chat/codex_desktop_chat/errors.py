"""All failures distinguish whether a request may already have been sent."""
class DesktopChatError(RuntimeError):
    def __init__(self, code, message, *, receipt_id=None, may_have_sent=False):
        super().__init__(message)
        self.code, self.receipt_id, self.may_have_sent = code, receipt_id, may_have_sent

    def as_dict(self):
        return {"code": self.code, "message": str(self), "receipt_id": self.receipt_id,
                "may_have_sent": self.may_have_sent}
