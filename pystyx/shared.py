from enum import Enum


class OnThrowValue(Enum):
    OrElse = "or_else"
    Throw = "throw"
    Skip = "skip"
