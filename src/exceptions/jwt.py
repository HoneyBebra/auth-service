class TokenError(Exception):
    default_message: str = "Token error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message if message is not None else self.default_message
        super().__init__(self.message)


class TokenMissingError(TokenError):
    default_message = "Credentials are not provided"


class TokenInvalidError(TokenError):
    default_message = "Invalid credentials"


class TokenExpiredError(TokenError):
    default_message = "Token is outdated"


class TokenRevokedError(TokenError):
    default_message = "Token in blacklist"


class TokenWrongTypeError(TokenError):
    default_message = "Wrong token type"
