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
            parsed_obj["preprocess"] = self.parse_preprocess(
                toml_obj.preprocess, parsed_obj
            )
        if toml_obj.get("postprocess"):
            parsed_obj["postprocess"] = self.parse_postprocess(
                toml_obj.postprocess, parsed_obj
            )
        return parsed_obj

    def _process(self, process, parsed_object):
        if isinstance(process.input_paths, list) and all(
            isinstance(element, str) for element in process.input_paths
        ):
            parsed_object.input_paths = process.input_paths
        else:
            raise TypeError("input_paths must be a list of strings.")

        if isinstance(process.output_path, str):
            parsed_object.output_path = process.output_path
        else:
            raise TypeError("output_path must be a string.")

        if process.function in TomlFunction._functions:
            parsed_object.function = process.function
        else:
            raise TypeError(f"unknown function: {process.function}")

        if process.get("or_else"):
            parsed_object.or_else = process.or_else

        if process.get("on_throw"):
            throw_action = {
                "or_else": OnThrowValue.OrElse,
                "throw": OnThrowValue.Throw,
                "skip": OnThrowValue.Skip,
            }.get(process.on_throw, None)
            if not throw_action:
                raise TypeError(f"Unknown 'on_throw' action given: {process.on_throw}")
            if throw_action == OnThrowValue.OrElse and not parsed_object.get("or_else"):
                raise TypeError(
                    "If 'on_throw' action is 'or_else', then 'or_else' must be defined."
                )
            parsed_object.on_throw = throw_action

        return parsed_object

    def parse_preprocess(self, preprocess, parsed_object):
        return self._process(preprocess, parsed_object)

    def parse_postprocess(self, postprocess, parsed_object):
        return self._process(postprocess, parsed_object)
