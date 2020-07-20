import pytest

from munch import Munch, munchify

from ..functions import TomlFunction, parse_json
from ..parser import Parser, PreprocessParser, PostprocessParser, FieldsParser


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
def preprocess_parser():
    return PreprocessParser()


@pytest.fixture
def postprocess_parser():
    return PostprocessParser()


@pytest.fixture
def fields_parser():
    return FieldsParser()


@pytest.fixture
def preprocessor_obj():
    return munchify(
        {
            "input_paths": ["foo.bar"],
            "output_path": "foo.bar",
            "function": "parse_json",
            "or_else": "{}",
            "on_throw": "throw",
        }
    )


@pytest.fixture
def fields_input_obj():
    return munchify(
        {
            "input_paths": ["foo.bar"],
            "output_path": "foo.bar",
            "function": "parse_json",
            "or_else": "{}",
            "on_throw": "throw",
        }
    )


@pytest.fixture
def fields_possible_paths_obj():
    return munchify(
        {
            "possible_paths": ["foo.bar"],
            "path_condition": {"field": "bar", "value": 1},
            "output_path": "foo.bar",
            "function": "parse_json",
            "or_else": "{}",
            "on_throw": "throw",
        }
    )


@pytest.fixture
def postprocessor_obj():
    return munchify(
        {
            "input_paths": ["foo.bar"],
            "output_path": "foo.bar",
            "function": "parse_json",
            "or_else": "{}",
            "on_throw": "throw",
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
    def test_parses_input_paths_successfully(self, preprocess_parser, preprocessor_obj):
        parsed_obj = preprocess_parser.parse(preprocessor_obj)
        assert parsed_obj["input_paths"] == preprocessor_obj.input_paths

    def test_missing_input_paths_raises(self, preprocess_parser, preprocessor_obj):
        del preprocessor_obj.input_paths
        with pytest.raises(AttributeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_nonlist_input_paths_raises(self, preprocess_parser, preprocessor_obj):
        preprocessor_obj.input_paths = 0
        with pytest.raises(TypeError, match="must be a list of strings"):
            preprocess_parser.parse(preprocessor_obj)

    def test_nonlist_of_strings_input_paths_raises(
        self, preprocess_parser, preprocessor_obj
    ):
        preprocessor_obj.input_paths = [0]
        with pytest.raises(TypeError, match="must be a list of strings"):
            preprocess_parser.parse(preprocessor_obj)

    def test_parses_output_path_successfully(self, preprocess_parser, preprocessor_obj):
        parsed_obj = preprocess_parser.parse(preprocessor_obj)
        assert parsed_obj["output_path"] == preprocessor_obj.output_path

    def test_missing_output_path_raises(self, preprocess_parser, preprocessor_obj):
        del preprocessor_obj.output_path
        with pytest.raises(AttributeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_nonstring_output_path_raises(self, preprocess_parser, preprocessor_obj):
        preprocessor_obj.output_path = 0
        with pytest.raises(TypeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_parse_function_successfully(self, preprocess_parser, preprocessor_obj):
        parsed_obj = preprocess_parser.parse(preprocessor_obj)
        assert parsed_obj["function"] == preprocessor_obj.function

    def test_unknown_function_raises(self, preprocess_parser, preprocessor_obj):
        preprocessor_obj.function = "unknown"
        with pytest.raises(TypeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_on_throw_parses_valid_enums(self, preprocess_parser, preprocessor_obj):
        from ..shared import OnThrowValue

        parsed_obj = preprocess_parser.parse(preprocessor_obj)
        assert parsed_obj["on_throw"].value == OnThrowValue.Throw.value

    def test_invalid_on_throw_raises(self, preprocess_parser, preprocessor_obj):
        preprocessor_obj.on_throw = "unknown"
        with pytest.raises(TypeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_optional_on_throw_skips(self, preprocess_parser, preprocessor_obj):
        del preprocessor_obj.on_throw
        preprocess_parser.parse(preprocessor_obj)

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, preprocess_parser, preprocessor_obj
    ):
        from ..shared import OnThrowValue

        preprocessor_obj.on_throw = "or_else"
        parsed_obj = preprocess_parser.parse(preprocessor_obj)
        assert parsed_obj["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(
        self, preprocess_parser, preprocessor_obj
    ):
        preprocessor_obj.on_throw = "or_else"
        del preprocessor_obj.or_else

        with pytest.raises(TypeError):
            preprocess_parser.parse(preprocessor_obj)

    def test_optional_or_else_skips(self, preprocess_parser, preprocessor_obj):
        del preprocessor_obj.or_else
        preprocess_parser.parse(preprocessor_obj)


class TestFields:
    def test_fields_is_required(self, parser, fields_input_obj):
        obj = Munch()
        with pytest.raises(TypeError, match="'fields' is a required field"):
            parser.parse(obj)

    def test_fields_input_paths_or_possible_paths_is_required(
        self, fields_parser, fields_input_obj, fields_possible_paths_obj
    ):
        fields_parser.parse(fields_input_obj)
        fields_parser.parse(fields_possible_paths_obj)
        no_paths_object = munchify({})
        with pytest.raises(
            TypeError, match="Either 'input_paths' or 'possible_paths' must be declared"
        ):
            fields_parser.parse(no_paths_object)

    def test_input_paths_and_possible_paths_cant_both_be_declared(
        self, fields_parser, fields_input_obj, fields_possible_paths_obj
    ):
        both_paths_object = munchify({"input_paths": [], "possible_paths": []})
        with pytest.raises(
            TypeError,
            match="Either 'input_paths' or 'possible_paths' must be declared, but not both.",
        ):
            fields_parser.parse(both_paths_object)

    def test_input_paths_is_list_of_strings(self, fields_parser, fields_input_obj):
        fields_parser.parse(fields_input_obj)

    def test_input_paths_not_list_raises(self, fields_parser, fields_input_obj):
        not_list_obj = munchify({"input_paths": 0})
        with pytest.raises(
            TypeError, match="input_paths must be a list of strings",
        ):
            fields_parser.parse(not_list_obj)

    def test_input_paths_not_list_of_strings_raises(
        self, fields_parser, fields_input_obj
    ):
        not_list_obj = munchify({"input_paths": [0]})
        with pytest.raises(
            TypeError, match="input_paths must be a list of strings",
        ):
            fields_parser.parse(not_list_obj)

    def test_potential_paths_is_list_of_strings(
        self, fields_parser, fields_possible_paths_obj
    ):
        fields_parser.parse(fields_possible_paths_obj)

    def test_potential_paths_not_list_raises(
        self, fields_parser, fields_possible_paths_obj
    ):
        not_list_obj = munchify({"possible_paths": 0})
        with pytest.raises(
            TypeError, match="possible_paths must be a list of strings",
        ):
            fields_parser.parse(not_list_obj)

    def test_potential_paths_not_list_of_strings_raises(
        self, fields_parser, fields_possible_paths_obj
    ):
        not_list_obj = munchify({"possible_paths": [0]})
        with pytest.raises(
            TypeError, match="possible_paths must be a list of strings",
        ):
            fields_parser.parse(not_list_obj)

    def test_paths_condition_is_required_if_possible_paths_is_set(
        self, fields_parser, fields_possible_paths_obj
    ):
        del fields_possible_paths_obj.path_condition
        with pytest.raises(
            TypeError, match="'path_condition' must be set if 'possible_paths' is set",
        ):
            fields_parser.parse(fields_possible_paths_obj)

    def test_type_is_optional(self, fields_parser, fields_input_obj):
        if hasattr(fields_input_obj, "type"):
            del fields_input_obj.type
        fields_parser.parse(fields_input_obj)

    def test_function_is_optional(self, fields_parser, fields_input_obj):
        if hasattr(fields_input_obj, "function"):
            del fields_input_obj.function
        fields_parser.parse(fields_input_obj)

    def test_or_else_is_optional(self, fields_parser, fields_input_obj):
        if hasattr(fields_input_obj, "or_else"):
            del fields_input_obj.or_else
        fields_parser.parse(fields_input_obj)

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, fields_parser, fields_input_obj
    ):
        from ..shared import OnThrowValue

        fields_input_obj.on_throw = "or_else"
        parsed_obj = fields_parser.parse(fields_input_obj)
        assert parsed_obj["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(
        self, fields_parser, fields_input_obj
    ):
        fields_input_obj.on_throw = "or_else"
        del fields_input_obj.or_else

        with pytest.raises(TypeError, match="'or_else' must be defined"):
            fields_parser.parse(fields_input_obj)

    @pytest.mark.skip
    def test_unknown_non_nested_keys_raises(self, fields_parser, fields_input_obj):
        fields_input_obj.on_throw = "hades"
        with pytest.raises(TypeError, match=f"Unknown key 'hades' on fields object"):
            fields_parser.parse(fields_input_obj)

    @pytest.mark.skip
    def test_nested_fields_require_parent_field_as_base(self):
        nested_obj = munchify({"fields.olympian": ""})
        pass


class TestPostprocess:
    def test_parses_input_paths_successfully(
        self, postprocess_parser, postprocessor_obj
    ):
        parsed_obj = postprocess_parser.parse(postprocessor_obj)
        assert parsed_obj["input_paths"] == postprocessor_obj.input_paths

    def test_missing_input_paths_raises(self, postprocess_parser, postprocessor_obj):
        del postprocessor_obj.input_paths
        with pytest.raises(AttributeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_nonlist_input_paths_raises(self, postprocess_parser, postprocessor_obj):
        postprocessor_obj.input_paths = 0
        with pytest.raises(TypeError, match="must be a list of strings"):
            postprocess_parser.parse(postprocessor_obj)

    def test_nonlist_of_strings_input_paths_raises(
        self, postprocess_parser, postprocessor_obj
    ):
        postprocessor_obj.input_paths = [0]
        with pytest.raises(TypeError, match="must be a list of strings"):
            postprocess_parser.parse(postprocessor_obj)

    def test_parses_output_path_successfully(
        self, postprocess_parser, postprocessor_obj
    ):
        parsed_obj = postprocess_parser.parse(postprocessor_obj)
        assert parsed_obj["output_path"] == postprocessor_obj.output_path

    def test_missing_output_path_raises(self, postprocess_parser, postprocessor_obj):
        del postprocessor_obj.output_path
        with pytest.raises(AttributeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_nonstring_output_path_raises(self, postprocess_parser, postprocessor_obj):
        postprocessor_obj.output_path = 0
        with pytest.raises(TypeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_parse_function_successfully(self, postprocess_parser, postprocessor_obj):
        parsed_obj = postprocess_parser.parse(postprocessor_obj)
        assert parsed_obj["function"] == postprocessor_obj.function

    def test_unknown_function_raises(self, postprocess_parser, postprocessor_obj):
        postprocessor_obj.function = "unknown"
        with pytest.raises(TypeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_on_throw_parses_valid_enums(self, postprocess_parser, postprocessor_obj):
        from ..shared import OnThrowValue

        parsed_obj = postprocess_parser.parse(postprocessor_obj)
        assert parsed_obj["on_throw"].value == OnThrowValue.Throw.value

    def test_invalid_on_throw_raises(self, postprocess_parser, postprocessor_obj):
        postprocessor_obj.on_throw = "unknown"
        with pytest.raises(TypeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_optional_on_throw_skips(self, postprocess_parser, postprocessor_obj):
        del postprocessor_obj.on_throw
        postprocess_parser.parse(postprocessor_obj)

    def test_on_throw_with_or_else_parses_or_else_successfully(
        self, postprocess_parser, postprocessor_obj
    ):
        from ..shared import OnThrowValue

        postprocessor_obj.on_throw = "or_else"
        parsed_obj = postprocess_parser.parse(postprocessor_obj)
        assert parsed_obj["on_throw"].value == OnThrowValue.OrElse.value

    def test_on_throw_with_or_else_missing_raises(
        self, postprocess_parser, postprocessor_obj
    ):
        postprocessor_obj.on_throw = "or_else"
        del postprocessor_obj.or_else

        with pytest.raises(TypeError):
            postprocess_parser.parse(postprocessor_obj)

    def test_optional_or_else_skips(self, postprocess_parser, postprocessor_obj):
        del postprocessor_obj.or_else
        postprocess_parser.parse(postprocessor_obj)