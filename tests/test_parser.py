import pytest

from munch import munchify

from ..functions import TomlFunction, parse_json
from ..parser import Parser


@pytest.fixture
def functions_obj():
    return munchify({"functions": ["parse_json"]})


@pytest.fixture
def TomlFunctionClass():
    cls = TomlFunction
    cls._functions = {"parse_json": parse_json}
    return cls


@pytest.fixture
def parser():
    return Parser()


@pytest.fixture
def preprocessor_obj():
    return munchify(
        {
            "preprocess": {
                "input_paths": ["foo.bar"],
                "output_path": "foo.bar",
                "function": "parseJson",
                "or_else": "{}",
                "on_throw": "throw",
            }
        }
    )


@pytest.fixture
def fields_input_obj():
    return munchify(
        {
            "fields": {
                "input_paths": ["foo.bar"],
                "output_path": "foo.bar",
                "function": "parseJson",
                "or_else": "{}",
                "on_throw": "throw",
            }
        }
    )


@pytest.fixture
def fields_possible_paths_obj():
    return munchify(
        {
            "fields": {
                "input_paths": ["foo.bar"],
                "output_path": "foo.bar",
                "function": "parseJson",
                "or_else": "{}",
                "on_throw": "throw",
            }
        }
    )


@pytest.fixture
def postprocessor_obj():
    return munchify(
        {
            "postprocess": {
                "input_path": ["foo.bar"],
                "output_path": "foo.bar",
                "function": "parseJson",
                "or_else": "{}",
                "on_throw": "throw",
            }
        }
    )


class TestFunctions:
    def test_functions_successfully_parsed_from_functions_styx(
        self, TomlFunctionClass, functions_obj
    ):
        functions_dict = TomlFunction.parse_functions(functions_obj)
        assert functions_dict["parse_json"] == parse_json

    def test_parse_function_raises_if_extra_declarations(
        self, TomlFunctionClass, functions_obj
    ):
        functions_obj.functions.append("unknown")
        with pytest.raises(TypeError, match="Function names were: unknown"):
            TomlFunction.parse_functions(functions_obj)

    def test_parse_function_raises_if_extra_decoratored_functions(
        self, TomlFunctionClass, functions_obj
    ):
        TomlFunctionClass._functions["other_function"] = lambda: None
        with pytest.raises(TypeError, match="Function names were: other_function"):
            TomlFunction.parse_functions(functions_obj)


class TestPreprocess:
    def test_parses_input_paths_successfully(self, parser, preprocessor_obj):
        parsed_obj = parser.parse(preprocessor_obj)
        assert (
            parsed_obj["preprocess"]["input_paths"]
            == preprocessor_obj.preprocess.input_paths
        )

    def test_missing_input_paths_raises(self, parser, preprocessor_obj):
        del preprocessor_obj.preprocess.input_paths
        with pytest.raises(AttributeError):
            parser.parse(preprocessor_obj)

    def test_nonlist_input_paths_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.input_paths = 0
        with pytest.raises(TypeError, match="must be a list of strings"):
            parser.parse(preprocessor_obj)

    def test_nonlist_of_strings_input_paths_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.input_paths = [0]
        with pytest.raises(TypeError, match="must be a list of strings"):
            parser.parse(preprocessor_obj)

    def test_parses_output_path_successfully(self, parser, preprocessor_obj):
        parsed_obj = parser.parse(preprocessor_obj)
        assert (
            parsed_obj["preprocess"]["output_path"]
            == preprocessor_obj.preprocess.output_path
        )

    def test_missing_output_path_raises(self, parser, preprocessor_obj):
        del preprocessor_obj.preprocess.output_path
        with pytest.raises(AttributeError):
            parser.parse(preprocessor_obj)

    def test_nonstring_output_path_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.output_path = 0
        with pytest.raises(TypeError):
            parser.parse(preprocessor_obj)

    def test_parse_function_successfully(self, parser, preprocessor_obj):
        parsed_obj = parser.parse(preprocessor_obj)
        assert (
            parsed_obj["preprocess"]["function"] == preprocessor_obj.preprocess.function
        )

    def test_unknown_function_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.function = "unknown"
        with pytest.raises(TypeError):
            parser.parse(preprocessor_obj)

    def test_on_throw_parses_valid_enums(self, parser, preprocessor_obj):
        from ..shared import OnThrowValue

        parsed_obj = parser.parse(preprocessor_obj)
        assert parsed_obj["preprocess"]["on_throw"].value == OnThrowValue.Throw.value

    def test_invalid_on_throw_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.on_throw = "unknown"
        with pytest.raises(TypeError):
            parser.parse(preprocessor_obj)

    def test_optional_on_throw_skips(self, parser, preprocessor_obj):
        del preprocessor_obj.preprocess.on_throw
        parser.parse(preprocessor_obj)

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, parser, preprocessor_obj
    ):
        from ..shared import OnThrowValue

        preprocessor_obj.preprocess.on_throw = "or_else"
        parsed_obj = parser.parse(preprocessor_obj)
        assert parsed_obj["preprocess"]["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(self, parser, preprocessor_obj):
        preprocessor_obj.preprocess.on_throw = "or_else"
        del preprocessor_obj.preprocess.or_else

        with pytest.raises(TypeError):
            parser.parse(preprocessor_obj)

    def test_optional_or_else_skips(self, parser, preprocessor_obj):
        del preprocessor_obj.preprocess.or_else
        parser.parse(preprocessor_obj)


class TestFields:
    def test_fields_is_required(self, fields_obj):
        pass

    def test_fields_input_paths_or_possible_paths_is_required(self, fields_obj):
        pass

    def test_input_paths_is_list(self, fields_obj):
        pass

    def test_input_paths_not_list_raises(self, fields_obj):
        pass

    def test_paths_condition_is_required_if_possible_paths_is_set(self, fields_obj):
        pass

    def test_type_is_optional(self, fields_obj):
        pass

    def test_function_is_optional(self, fields_obj):
        pass

    def test_or_else_is_optional(self, fields_obj):
        pass

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, parser, postprocessor_obj
    ):
        from ..shared import OnThrowValue

        postprocessor_obj.postprocess.on_throw = "or_else"
        parsed_obj = parser.parse(postprocessor_obj)
        assert parsed_obj["postprocess"]["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.on_throw = "or_else"
        del postprocessor_obj.postprocess.or_else

        with pytest.raises(TypeError):
            parser.parse(postprocessor_obj)

    def test_nested_fields_require_parent_field_as_base(self):
        pass


class TestPostprocess:
    def test_parses_input_paths_successfully(self, parser, postprocessor_obj):
        parsed_obj = parser.parse(postprocessor_obj)
        assert (
            parsed_obj["postprocess"]["input_paths"]
            == postprocessor_obj.postprocess.input_paths
        )

    def test_missing_input_paths_raises(self, parser, postprocessor_obj):
        del postprocessor_obj.postprocess.input_paths
        with pytest.raises(AttributeError):
            parser.parse(postprocessor_obj)

    def test_nonlist_input_paths_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.input_paths = 0
        with pytest.raises(TypeError, match="must be a list of strings"):
            parser.parse(postprocessor_obj)

    def test_nonlist_of_strings_input_paths_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.input_paths = [0]
        with pytest.raises(TypeError, match="must be a list of strings"):
            parser.parse(postprocessor_obj)

    def test_parses_output_path_successfully(self, parser, postprocessor_obj):
        parsed_obj = parser.parse(postprocessor_obj)
        assert (
            parsed_obj["postprocess"]["output_path"]
            == postprocessor_obj.postprocess.output_path
        )

    def test_missing_output_path_raises(self, parser, postprocessor_obj):
        del postprocessor_obj.postprocess.output_path
        with pytest.raises(AttributeError):
            parser.parse(postprocessor_obj)

    def test_nonstring_output_path_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.output_path = 0
        with pytest.raises(TypeError):
            parser.parse(postprocessor_obj)

    def test_parse_function_successfully(self, parser, postprocessor_obj):
        parsed_obj = parser.parse(postprocessor_obj)
        assert (
            parsed_obj["postprocess"]["function"]
            == postprocessor_obj.postprocess.function
        )

    def test_unknown_function_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.function = "unknown"
        with pytest.raises(TypeError):
            parser.parse(postprocessor_obj)

    def test_on_throw_parses_valid_enums(self, parser, postprocessor_obj):
        from ..shared import OnThrowValue

        parsed_obj = parser.parse(postprocessor_obj)
        assert parsed_obj["postprocess"]["on_throw"].value == OnThrowValue.Throw.value

    def test_invalid_on_throw_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.on_throw = "unknown"
        with pytest.raises(TypeError):
            parser.parse(postprocessor_obj)

    def test_optional_on_throw_skips(self, parser, postprocessor_obj):
        del postprocessor_obj.postprocess.on_throw
        parser.parse(postprocessor_obj)

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, parser, postprocessor_obj
    ):
        from ..shared import OnThrowValue

        postprocessor_obj.postprocess.on_throw = "or_else"
        parsed_obj = parser.parse(postprocessor_obj)
        assert parsed_obj["postprocess"]["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(self, parser, postprocessor_obj):
        postprocessor_obj.postprocess.on_throw = "or_else"
        del postprocessor_obj.postprocess.or_else

        with pytest.raises(TypeError):
            parser.parse(postprocessor_obj)

    def test_optional_or_else_skips(self, parser, postprocessor_obj):
        del postprocessor_obj.postprocess.or_else
        parser.parse(postprocessor_obj)
