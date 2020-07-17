from typing import Callable, Dict, List

from munch import Munch, munchify
from pydash import get, set_

from .functions import TomlFunction
from .parser import Parser


def empty_functions_toml():
    return munchify({"functions": []})


class Mapper:
    functions: Dict[str, Callable]
    map: Munch
    mapped_object: any
    maps: Dict[str, Munch]
    raw_map: Munch
    type: str

    def __init__(self, toml_map, functions, maps=None):
        self.raw_map = toml_map
        self.map = self.parse_map(self.raw_map)
        self.mapped_object = {}  # TOOD: Allow for other structures
        self.type = self.map.type
        self.maps = maps if maps is not None else {}
        self.functions = functions

    def __call__(self, blob: any):
        blob = self.preprocess(blob)
        blob = self.fields(blob)
        blob = self.postprocess(blob)
        return blob

    def parse_map(self, toml_map: Munch) -> Munch:
        parser = Parser()
        return parser.parse(toml_map)

    def preprocess(self, blob):
        if self.map.preprocess:
            preprocessors = sorted(
                [(key, value) for key, value in self.map.preprocess.items()],
                key=lambda pair: pair[0],
            )
            for (_key, preprocessor) in preprocessors:
                func = self.functions[preprocessor.transform]
                old_value = get(
                    blob,
                    preprocessor.path,
                    preprocessor.or_else if preprocessor.or_else else None,
                )
                new_value = func(old_value)
                set_(blob, preprocessor.path, new_value)
            return blob

    def fields(self, blob):
        for field, action in self.map.fields.items():
            if action.get("input_path") and action.get("input_path_options"):
                raise RuntimeError(
                    "input_path and input_path_options cannot both be defined."
                )

            if action.get("input_path_options"):
                options = [get(blob, path, None) for path in action.input_path_options]
                condition = action.options_condition
                potential_values = list(
                    filter(
                        lambda val: get(val, condition.field) == condition.value,
                        options,
                    )
                )

                if len(potential_values) > 1:
                    raise RuntimeError(
                        "Unable to determine input path. Found more than one option satisfying predicate."
                    )

                if not potential_values:
                    raise RuntimeError(
                        "Unable to determine input path. Unable to find option satisfying predicate."
                    )

                value = potential_values[0]
                # TODO: Pass off Foreign key to other TOML Object (Address) for handling
            else:
                value = get(blob, action.input_path)

            set_(self.mapped_object, action.output_path, value)
        return self.mapped_object

    def postprocess(self, blob):
        # TODO
        return self.mapped_object
