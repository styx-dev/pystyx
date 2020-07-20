"""
Parse, don't validate. - Alexis King
"""
from munch import Munch

from .functions import TomlFunction
from .shared import OnThrowValue


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
            throw_action = {
                "or_else": OnThrowValue.OrElse,
                "throw": OnThrowValue.Throw,
                "skip": OnThrowValue.Skip,
            }.get(process.on_throw, None)
            if not throw_action:
                raise TypeError(f"Unknown 'on_throw' action given: {process.on_throw}")
            if throw_action == OnThrowValue.OrElse and not process_obj.get("or_else"):
                raise TypeError(
                    "If 'on_throw' action is 'or_else', then 'or_else' must be defined."
                )
            process_obj.on_throw = throw_action

        return process_obj

    def parse_preprocess(self, preprocess):
        return self._process(preprocess)

    def parse_fields(self, fields):
        fields_obj = Munch()
        return fields_obj

    def parse_postprocess(self, postprocess):
        return self._process(postprocess)
