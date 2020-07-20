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


class Parser:
    def parse(self, toml_obj: Munch):
        parsed_obj = Munch()
        if toml_obj.get("preprocess"):
            parsed_obj["preprocess"] = self.parse_preprocess(toml_obj.preprocess)

        if not hasattr(toml_obj, "fields"):
            raise TypeError(
                "'fields' is a required field for a Styx definition mapping."
            )
        parsed_obj["fields"] = self.parse_fields(toml_obj.fields)

        if toml_obj.get("postprocess"):
            parsed_obj["postprocess"] = self.parse_postprocess(toml_obj.postprocess)
        return parsed_obj

    def _process(self, process):
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

    def parse_preprocess(self, preprocess):
        return self._process(preprocess)

    def parse_fields(self, fields):
        fields_obj = Munch()

        if not hasattr(fields, "input_paths") and not hasattr(fields, "possible_paths"):
            raise TypeError(
                "Either 'input_paths' or 'possible_paths' must be declared. Aborting."
            )

        if hasattr(fields, "input_paths") and hasattr(fields, "possible_paths"):
            raise TypeError(
                "Either 'input_paths' or 'possible_paths' must be declared, but not both."
            )

        if hasattr(fields, "input_paths"):
            if isinstance(fields.input_paths, list) and all(
                isinstance(element, str) for element in fields.input_paths
            ):
                fields_obj.input_paths = fields.input_paths

            else:
                raise TypeError("input_paths must be a list of strings.")
        else:
            if isinstance(fields.possible_paths, list) and all(
                isinstance(element, str) for element in fields.possible_paths
            ):
                if not fields.get("path_condition"):
                    raise TypeError(
                        "'path_condition' must be set if 'possible_paths' is set."
                    )
                fields_obj.possible_paths = fields.possible_paths

            else:
                raise TypeError("possible_paths must be a list of strings.")

        if fields.get("or_else"):
            fields_obj.or_else = fields.or_else

        if fields.get("on_throw"):
            throw_action = parse_on_throw(fields, fields_obj)
            fields_obj.on_throw = throw_action

        return fields_obj

    def parse_postprocess(self, postprocess):
        return self._process(postprocess)
