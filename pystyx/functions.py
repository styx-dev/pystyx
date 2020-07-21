import json
from typing import Callable, Dict

from munch import munchify

# Adapted from this response in Stackoverflow
# http://stackoverflow.com/a/19053800/1072990
def _to_camel_case(snake_str):
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    return components[0] + "".join(x.capitalize() if x else "_" for x in components[1:])


class TomlFunction:
    _functions: Dict[str, Callable] = {}

    @staticmethod
    def _parse_functions(functions_toml):
        declared_functions = set(functions_toml.functions)
        decorated_functions = set(TomlFunction._functions.keys())

        extra_declared_functions = declared_functions - decorated_functions
        extra_decorated_functions = decorated_functions - declared_functions

        if extra_declared_functions:
            functions = ", ".join(
                sorted(func_name for func_name in extra_declared_functions)
            )
            msg = f"Found extra functions in functions.styx that were not defined!\nFunction names were: {functions}"
            raise TypeError(msg)

        if extra_decorated_functions:
            functions = ", ".join(
                sorted(func_name for func_name in extra_decorated_functions)
            )
            msg = f"Found extra functions decorated with @toml_function that were not declared in functions.styx!\nFunction names were: {functions}"
            raise TypeError(msg)

        return TomlFunction._functions

    @staticmethod
    def parse_functions(functions_toml):
        if hasattr(functions_toml, "functions"):
            if not isinstance(functions_toml.functions, list):
                raise TypeError(
                    "functions.styx was malformed. 'functions' key must be a list."
                )
            return TomlFunction._parse_functions(functions_toml)
        else:
            raise TypeError("functions.styx was malformed. No 'functions' list found.")


class styx_function:
    function: Callable
    _functions = {}

    def __init__(self, function: Callable):
        self.function = function
        function_name = function.__name__
        if function_name in TomlFunction._functions:
            raise RuntimeError(
                f"Duplicate name found in toml_functions: {function_name}"
            )
        TomlFunction._functions[function_name] = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


@styx_function
def to_camel_case(snake_str):
    return _to_camel_case(snake_str)


@styx_function
def parse_json(s):
    return munchify(json.loads(s))


@styx_function
def parse_bool(s):
    return s.lower() in ("true", "1", "t", "y", "yes")
