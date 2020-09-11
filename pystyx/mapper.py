from typing import Callable, Dict, Literal

from munch import Munch, munchify
from pydash import get, set_

from .parser import Parser
from .shared import OnThrowValue, parse_const


def empty_functions_toml():
    return munchify({"functions": []})


def handle_exception(definition, exc):
    on_throw_enum = definition.get("on_throw")
    on_throw_enum_value = getattr(on_throw_enum, "value", None)
    if on_throw_enum_value == OnThrowValue.Skip.value:
        return None, True
    elif on_throw_enum_value == OnThrowValue.OrElse.value:
        return definition.or_else, False
    else:
        raise exc


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
                many = processor.pop("many")
                if many:
                    objs = obj
                    obj = [self.process(obj, processor) for obj in objs]
                else:
                    obj = self.process(obj, processor)

        return obj

    def process(self, obj, processor):
        if processor.input_paths == ["."]:
            old_values = [obj]
        else:
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
            (new_value, skip) = handle_exception(processor, exc)
            if skip:
                return obj

        obj = self.output_value(obj, processor.output_path, new_value)
        return obj

    def output_value(self, obj, output_path, new_value):
        if output_path == ".":
            # Allows changing the entire structure by using the 'cwd' alias
            return new_value
        else:
            return set_(obj, output_path, new_value)


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
        # TODO: Add other structures potentially besides JSON
        type_ = self.definition.__type__
        if type_ == "object":
            if self.definition.include_type:
                to_obj = {"__type__": self.definition.to_type}
            else:
                to_obj = {}
        elif type_ == "list":
            to_obj = []
        else:
            raise RuntimeError(
                f"Unknown type declaration found: {type_}. How did the parser not catch this?"
            )

        many = self.definition.fields["many"]

        if many:
            from_objs = from_obj
            return [self._map(from_obj, to_obj) for from_obj in from_objs]
        else:
            return self._map(from_obj, to_obj)

    def _map(self, from_obj, to_obj):
        for field_name, field_definition in self.definition.fields.items():
            if field_name == "many":
                continue
            to_obj = self.map_field(from_obj, to_obj, field_name, field_definition)
        return to_obj

    def map_field(self, from_obj, to_obj, field_name, field_definition):
        (value, skip) = self.get_field_value(field_name, from_obj, field_definition)
        if not skip:
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

            (value, skip) = self.apply_function_to_values(
                field_definition, potential_values
            )
        else:
            (value, skip) = self.apply_function(field_definition, from_obj)

        if skip:
            return None, skip

        if field_definition.get("from_type"):
            value = self.map_nested_type(field_name, field_definition, from_obj, value)

        if field_definition.get("mapping"):
            mapping = field_definition.get("mapping")
            default = mapping.get("__default__")
            value = mapping.get(value, default)

        return value, False

    def map_nested_type(self, field_name, field_definition, from_obj, value):
        nested_mapper = self.definitions.get(field_definition.from_type)
        if not nested_mapper:
            raise RuntimeError(
                f"Unable to map nested object. Unknown type: {field_definition.from_type}"
            )

        extended_value = self.copy_fields(field_name, field_definition, from_obj, value)
        return nested_mapper(extended_value)

    def copy_fields(self, field_name, field_definition, from_obj, value):
        """
        Non-reserved words are used to copy extra data to the nested object for mapping
        """
        for key in field_definition._copy_fields:
            path = get(field_definition, [field_name, key])
            s, is_const = parse_const(path)
            if is_const:
                value[key] = s
            else:
                value[key] = get(from_obj, path)

        return value

    def apply_function(self, field_definition, from_obj):
        values = []
        for path in field_definition.input_paths:
            value, is_const = parse_const(path)
            values.append(value if is_const else get(from_obj, path, None))

        return self.apply_function_to_values(field_definition, values)

    def apply_function_to_values(self, field_definition, values):
        try:
            skip = False
            if field_definition.get("function"):
                return field_definition.function(*values), skip
            else:
                value = values[0]
                if value is None:
                    raise ValueError(f"No value found for path.")
                return value, skip
        except Exception as e:
            return handle_exception(field_definition, e)


class Mapper:
    definition: Munch
    definitions: Dict[str, Munch]
    fieldsMapper: FieldsMapper
    fieldsMapperClass = FieldsMapper
    from_type: str
    functions: Dict[str, Callable]
    preprocessMapper: PreprocessMapper
    preprocessMapperClass = PreprocessMapper
    postprocessMapper: PostprocessMapper
    postprocessMapperClass = PostprocessMapper
    raw_map: Munch
    to_type: str

    def __init__(self, toml_map, functions, definitions=None):
        self.raw_map = toml_map
        (self.from_type, self.to_type, self.definition) = self.parse_definition(
            self.raw_map
        )
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
        return f"<Mapper: {self.from_type} -> {self.to_type}>"

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
