class RateLimitError(Exception):
    default_message = "Rate limit error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message if message is not None else self.default_message
        super().__init__(self.message)


class RateLimitExceeded(RateLimitError):
    default_message = "Rate limit exceeded"


class AccountLocked(RateLimitError):
    default_message = "Account is temporarily blocked"
