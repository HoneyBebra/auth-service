from typing import Any


class WrongParams(Exception):
    def __init__(self, params: list[Any]) -> None:
        self.message = f"Wrong params: {params}"
