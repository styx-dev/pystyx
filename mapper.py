from typing import Callable, Dict, Literal

from munch import Munch, munchify
from pydash import get, set_

from .parser import Parser


def empty_functions_toml():
    return munchify({"functions": []})


class ProcessMapper:
    definition: Munch
    definitions: Dict[str, Munch]
    functions: Dict[str, Callable]
    processor_key: Literal["preprocess", "postprocess"] = NotImplementedError

    def __init__(self, definition, functions, definitions):
        self.definition = definition
        self.definitions = definitions
        self.functions = functions

    def __call__(self, obj):
        """
        Depending on whether it is preprocess or postprocess,
        the obj will either be the from_obj or the to_obj.

        That is, preprocess prepares the from_obj for processing.
        Postprocess polishes the to_obj for final export.
        """
        if self.definition.get(self.processor_key):
            process_dict = getattr(self.definition, self.processor_key)
            processors = sorted(
                [(key, value) for key, value in process_dict.items()],
                key=lambda pair: pair[0],
            )
            for (_key, processor) in processors:
                func = self.functions[processor.transform]
                old_value = get(
                    obj,
                    processor.path,
                    processor.or_else if processor.or_else else None,
                )
                new_value = func(old_value)
                set_(obj, processor.path, new_value)
            return obj


class PreprocessMapper(ProcessMapper):
    processor_key = "preprocess"


class PostprocessMapper(ProcessMapper):
    processor_key = "postprocess"


class FieldsMapper:
    definition: Munch
    definitions: Dict[str, Munch]
    functions: Dict[str, Callable]

    def __init__(self, definition, functions, definitions):
        self.definition = definition
        self.definitions = definitions
        self.functions = functions

    def __call__(self, from_obj):
        to_obj = {}  # TODO: Add other structures potentially

        for field_name, field_definition in self.definition.fields.items():
            to_obj = self.map_field(from_obj, to_obj, field_name, field_definition)

        return to_obj

    def map_field(self, from_obj, to_obj, field_name, field_definition):
        value = self.get_field_value(from_obj, field_definition)
        set_(to_obj, field_name, value)
        return to_obj

    def get_field_value(self, from_obj, field_definition):
        if field_definition.get("possible_paths"):
            options = [
                get(from_obj, path, None)
                for path in field_definition.input_path_options
            ]
            condition = field_definition.options_condition
            potential_values = list(
                filter(
                    lambda val: get(val, condition.field) == condition.value, options,
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
        else:
            value = get(from_obj, field_definition.input_path)

        # TODO: Pass off Foreign key to other TOML Object (Address) for handling
        return value


class Mapper:
    definition: Munch
    definitions: Dict[str, Munch]
    fieldsMapper: FieldsMapper
    fieldsMapperClass = FieldsMapper
    functions: Dict[str, Callable]
    preprocessMapper: PreprocessMapper
    preprocessMapperClass = PreprocessMapper
    postprocessMapper: PostprocessMapper
    postprocessMapperClass = PostprocessMapper
    raw_map: Munch
    type: str

    def __init__(self, toml_map, functions, definitions=None):
        self.raw_map = toml_map
        (self.type, self.definition) = self.parse_definition(self.raw_map)
        self.definitions = definitions if definitions is not None else {}
        self.functions = functions

        self.preprocessMapper = self.preprocessMapperClass(
            self.definition, functions, self.definitions
        )
        self.fieldsMapper = self.fieldsMapperClass(
            self.definition, functions, self.definitions
        )
        self.postprocessMapper = self.postprocessMapperClass(
            self.definition, functions, self.definitions
        )

    def __call__(self, from_obj: any):
        from_obj = self.preprocessMapper(from_obj)
        to_obj = self.fieldsMapper(from_obj)
        to_obj = self.postprocessMapper(to_obj)
        return to_obj

    def parse_definition(self, toml_map: Munch) -> Munch:
        parser = Parser()
        return parser.parse(toml_map)
