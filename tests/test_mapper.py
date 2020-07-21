import pytest

from munch import Munch, munchify

from ..functions import parse_json
from ..mapper import PreprocessMapper, PostprocessMapper, FieldsMapper


@pytest.fixture
def definitions():
    return munchify({})


@pytest.fixture
def functions():
    return munchify({"parse_json": parse_json, "concat": lambda a, b: a + b})


@pytest.fixture
def preprocess_definition():
    return munchify(
        {
            "preprocess": {
                "01_parse_title": {
                    "input_paths": ["fields.nested.title"],
                    "output_path": "fields.title",
                    "function": "parse_json",
                    "or_else": {},
                    "on_throw": "throw",
                },
                "02_concat_name": {
                    "input_paths": ["fields.first_name", "fields.last_name"],
                    "output_path": "fields.full_name",
                    "function": "concat",
                    "or_else": {},
                    "on_throw": "throw",
                },
                "03_silly_name": {
                    "input_paths": ["fields.title.title", "fields.last_name"],
                    "output_path": "fields.silly_name",
                    "function": "concat",
                    "or_else": {},
                    "on_throw": "throw",
                },
            }
        }
    )


@pytest.fixture
def blob():
    return munchify(
        {
            "fields": {
                "nested": {"title": '{"title": "foo"}',},
                "first_name": "Hera",
                "last_name": "cles",
            }
        }
    )


class TestPreprocessMapper:
    def test_single_argument_function(
        self, preprocess_definition, functions, definitions, blob
    ):
        mapper = PreprocessMapper(preprocess_definition, functions, definitions)
        result = mapper(blob)
        assert result.fields.title == munchify({"title": "foo"})

    def test_multiple_argument_function(
        self, preprocess_definition, functions, definitions, blob
    ):
        mapper = PreprocessMapper(preprocess_definition, functions, definitions)
        result = mapper(blob)
        assert result.fields.full_name == "Heracles"

    def test_functions_are_applied_in_alphanumeric_order(
        self, preprocess_definition, functions, definitions, blob
    ):
        mapper = PreprocessMapper(preprocess_definition, functions, definitions)
        result = mapper(blob)
        assert result.fields.silly_name == "foocles"

    def test_or_else_correctly_sets_value(self):
        pass

    def test_on_throw_skip_enum(self):
        pass

    def test_on_throw_or_else_enum(self):
        pass

    def test_on_throw_raise_enum(self):
        pass


class TestFieldsMapper:
    pass


class TestPostprocessMapper:
    pass
