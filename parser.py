"""
Parse, don't validate. - Alexis King
"""
from munch import Munch

from .functions import TomlFunction
from .shared import OnThrowValue


def parse_on_throw(from_obj, to_obj):
    """
    Expects "or_else" to already have been processed on "to_obj"
    """
    throw_action = {
        "or_else": OnThrowValue.OrElse,
        "throw": OnThrowValue.Throw,
        "skip": OnThrowValue.Skip,
    }.get(from_obj.on_throw, None)
    if not throw_action:
        raise TypeError(f"Unknown 'on_throw' action given: {from_obj.on_throw}")
    if throw_action == OnThrowValue.OrElse and not to_obj.get("or_else"):
        raise TypeError(
            "If 'on_throw' action is 'or_else', then 'or_else' must be defined."
        )
    return throw_action


class ProcessParser:
    def process(self, process):
        process_obj = Munch()
        if isinstance(process.input_paths, list) and all(
            isinstance(element, str) for element in process.input_paths
        ):
            process_obj.input_paths = process.input_paths
        else:
            raise TypeError("input_paths must be a list of strings.")

        if isinstance(process.output_path, str):
            process_obj.output_path = process.output_path
        else:
            raise TypeError("output_path must be a string.")

        if process.function in TomlFunction._functions:
            process_obj.function = process.function
        else:
            raise TypeError(f"unknown function: {process.function}")

        if process.get("or_else"):
            process_obj.or_else = process.or_else

        if process.get("on_throw"):
            throw_action = parse_on_throw(process, process_obj)
            process_obj.on_throw = throw_action

        return process_obj


class PreprocessParser(ProcessParser):
    def parse(self, preprocess):
        return self.process(preprocess)


class PostprocessParser(ProcessParser):
    def parse(self, postprocess):
        return self.process(postprocess)


class FieldsParser:
    reserved_words = {
        "input_paths",
        "possible_paths",
        "path_condition",
        "type",
        "function",
        "or_else",
        "on_throw",
    }

    def parse(self, fields):
        field_objs = Munch()

        if not fields:
            raise TypeError("'fields' cannot be empty (what are we mapping?)")

        for field_name, field in fields.items():
            field_obj = self.parse_field(field)
            field_objs[field_name] = self.parse_extra_fields(
                field_name, field, field_obj
            )

        return field_objs

    def parse_field(self, field):
        field_obj = Munch()

        field_obj = self.parse_paths(field, field_obj)

        if field.get("or_else"):
            field_obj.or_else = field.or_else

        if field.get("on_throw"):
            throw_action = parse_on_throw(field, field_obj)
            field_obj.on_throw = throw_action

        return field_obj

    def parse_paths(self, field, field_obj):
        if not hasattr(field, "input_paths") and not hasattr(field, "possible_paths"):
            raise TypeError(
                "Either 'input_paths' or 'possible_paths' must be declared. Aborting."
            )

        if hasattr(field, "input_paths") and hasattr(field, "possible_paths"):
            raise TypeError(
                "Either 'input_paths' or 'possible_paths' must be declared, but not both."
            )

        if hasattr(field, "input_paths"):
            if isinstance(field.input_paths, list) and all(
                isinstance(element, str) for element in field.input_paths
            ):
                field_obj.input_paths = field.input_paths

            else:
                raise TypeError("input_paths must be a list of strings.")
        else:
            if isinstance(field.possible_paths, list) and all(
                isinstance(element, str) for element in field.possible_paths
            ):
                if not field.get("path_condition"):
                    raise TypeError(
                        "'path_condition' must be set if 'possible_paths' is set."
                    )
                field_obj.possible_paths = field.possible_paths

            else:
                raise TypeError("possible_paths must be a list of strings.")

        return field_obj

    def parse_extra_fields(self, field_name, field, field_obj):
        """
        Handle non-reserved keywords on the Field object

        For now, the only allowed non-reserved keyword is the parent's field_name
        """
        for key, value in field.items():
            if key in self.reserved_words:
                continue

            if key != field_name:
                raise TypeError(f"Unknown key found on field definition: {field_name}")

            field_obj[key] = value

        return field_obj


class Parser:
    def parse(self, toml_obj: Munch):
        parsed_obj = Munch()
        if toml_obj.get("preprocess"):
            parser = PreprocessParser()
            parsed_obj["preprocess"] = parser.parse(toml_obj.preprocess)

        if not hasattr(toml_obj, "fields"):
            raise TypeError(
                "'fields' is a required field for a Styx definition mapping."
            )
        parsed_obj["fields"] = self.parse_fields(toml_obj.fields)

        if toml_obj.get("postprocess"):
            parser = PostprocessParser()
            parsed_obj["postprocess"] = parser.parse(toml_obj.postprocess)
        return parsed_obj
