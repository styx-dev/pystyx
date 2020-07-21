from typing import Callable, Dict, Literal

from munch import Munch, munchify
from pydash import get, set_

from .parser import Parser
from .shared import OnThrowValue


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
                old_values = (
                    get(
                        obj,
                        path,
                        processor.or_else if hasattr(processor, "or_else") else None,
                    )
                    for path in processor.input_paths
                )

                try:
                    new_value = processor.function(*old_values)
                except Exception as exc:
                    (new_value, skip) = self.handle_exception(processor, exc)
                    if skip:
                        continue

                set_(obj, processor.output_path, new_value)

        return obj

    def handle_exception(self, processor, exc):
        on_throw_enum = processor.get("on_throw")
        if on_throw_enum.value == OnThrowValue.Skip.value:
            return None, True
        elif on_throw_enum.value == OnThrowValue.OrElse.value:
            return processor.or_else, False
        else:
            raise exc


class PreprocessMapper(ProcessMapper):
    processor_key = "preprocess"


class PostprocessMapper(ProcessMapper):
    processor_key = "postprocess"


class FieldsMapper:
    definition: Munch
    definitions: Dict[str, "Mapper"]
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
        value = self.get_field_value(field_name, from_obj, field_definition)
        set_(to_obj, field_name, value)
        return to_obj

    def get_field_value(self, field_name, from_obj, field_definition):
        if field_definition.get("possible_paths"):
            options = [
                get(from_obj, path, None) for path in field_definition.possible_paths
            ]
            condition = field_definition.path_condition
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

            value = self.apply_function_to_values(
                field_definition, iter(potential_values)
            )
        else:
            value = self.apply_function(field_definition, from_obj)

        if field_definition.get("type"):
            value = self.map_nested_type(field_name, field_definition, from_obj, value)

        return value

    def map_nested_type(self, field_name, field_definition, from_obj, value):
        nested_mapper = self.definitions.get(field_definition.type)
        if not nested_mapper:
            raise RuntimeError(
                f"Unable to map nested object. Unknown type: {field_definition.type}"
            )

        extended_value = self.copy_fields(field_name, field_definition, from_obj, value)
        return nested_mapper(extended_value)

    def copy_fields(self, field_name, field_definition, from_obj, value):
        """
        Non-reserved words are used to copy extra data to the nested object for mapping
        """
        for key in field_definition._copy_fields:
            path = get(field_definition, [field_name, key])
            value[key] = get(from_obj, path)

        return value

    def apply_function(self, field_definition, from_obj):
        or_else = (
            field_definition.or_else if hasattr(field_definition, "or_else") else None
        )
        values = (get(from_obj, path, or_else) for path in field_definition.input_paths)
        return self.apply_function_to_values(field_definition, values)

    def apply_function_to_values(self, field_definition, values):
        if field_definition.get("function"):
            return field_definition.function(*values)
        else:
            return next(values)


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

    def __str__(self):
        return f"{self.definition.type}Mapper"

    def __repr__(self):
        return self.__str__()

    def parse_definition(self, toml_map: Munch) -> Munch:
        parser = Parser()
        return parser.parse(toml_map)

    def update_definitions(self, definitions):
        """
        Mutation. Sets definitions after creating all of them instead of using a global variable
        """
        self.definitions = definitions
        self.preprocessMapper.definitions = definitions
        self.fieldsMapper.definitions = definitions
        self.postprocessMapper.definitions = definitions
