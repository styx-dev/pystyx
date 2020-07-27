from enum import Enum


class OnThrowValue(Enum):
    OrElse = "or_else"
    Throw = "throw"
    Skip = "skip"


def parse_const(s):
    is_const = False
    if s.startswith("const('") and s.endswith("')"):
        is_const = True
        return s[7:-2], is_const
    return s, is_const
