"""Behavioral coverage for JSON traversal and standard-library compatibility."""

import io
import json
import math
import unittest

import JSON


class ParseTests(unittest.TestCase):
    def test_requested_javascript_style_traversal(self):
        obj = JSON.parse('[{"key": {"value": "hello"}}]')

        self.assertEqual(obj[0].key.value, "hello")
        self.assertEqual(obj[0]["key"]["value"], "hello")

    def test_nested_arrays_objects_and_iteration(self):
        obj = JSON.parse(
            '{"groups": [[{"profile": {"name": "Ada"}}, '
            '{"profile": {"name": "Lin"}}]], "empty": {}}'
        )

        self.assertEqual(obj.groups[0][0].profile.name, "Ada")
        self.assertEqual(
            [entry.profile.name for entry in obj.groups[0]], ["Ada", "Lin"]
        )
        self.assertIs(type(obj.groups), list)
        self.assertIsInstance(obj, dict)
        self.assertIsInstance(obj.empty, JSON.JSONObject)
        self.assertEqual(obj.empty, {})

    def test_scalars_remain_native_python_values(self):
        cases = [
            ('"hello"', "hello", str),
            ("42", 42, int),
            ("-3.5", -3.5, float),
            ("true", True, bool),
            ("false", False, bool),
            ("null", None, type(None)),
        ]
        for text, expected, expected_type in cases:
            with self.subTest(text=text):
                result = JSON.parse(text)
                self.assertEqual(result, expected)
                self.assertIs(type(result), expected_type)

    def test_mixed_array_and_empty_array(self):
        obj = JSON.parse('[null, false, 0, "", [], {}, {"value": 2}]')

        self.assertEqual(obj[:6], [None, False, 0, "", [], {}])
        self.assertEqual(obj[-1].value, 2)
        self.assertIs(type(JSON.parse("[]")), list)

    def test_large_integer_remains_exact(self):
        value = 9007199254740993
        self.assertEqual(JSON.parse(str(value)), value)

    def test_unicode_and_escaped_characters(self):
        obj = JSON.parse('{"café": "雪", "message": "line\\n\\\"quoted\\\""}')

        self.assertEqual(obj.café, "雪")
        self.assertEqual(obj.message, 'line\n"quoted"')

    def test_byte_input(self):
        for source in (b'{"value": 7}', bytearray(b'{"value": 7}')):
            with self.subTest(source_type=type(source)):
                self.assertEqual(JSON.parse(source).value, 7)

    def test_loads_alias(self):
        self.assertIs(JSON.loads, JSON.parse)
        self.assertEqual(JSON.loads('{"value": 7}').value, 7)

    def test_load_reads_text_and_binary_streams(self):
        for source in (io.StringIO('{"value": 7}'), io.BytesIO(b'{"value": 7}')):
            with source, self.subTest(source_type=type(source)):
                self.assertEqual(JSON.load(source).value, 7)
                self.assertFalse(source.closed)

    def test_duplicate_keys_follow_decoder_last_value_behavior(self):
        self.assertEqual(JSON.parse('{"value": 1, "value": 2}').value, 2)

    def test_invalid_json_preserves_decode_error_details(self):
        invalid_documents = ("", "{", "[1,]", '{"value":}', "{} {}")
        for document in invalid_documents:
            with self.subTest(document=document):
                with self.assertRaises(JSON.JSONDecodeError) as raised:
                    JSON.parse(document)
                self.assertEqual(raised.exception.doc, document)
                self.assertGreaterEqual(raised.exception.pos, 0)
        self.assertIs(JSON.JSONDecodeError, json.JSONDecodeError)

    def test_nonstandard_numeric_constants_are_rejected_at_any_depth(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            for document in (constant, f'{{"values": [{constant}]}}'):
                with self.subTest(document=document):
                    with self.assertRaisesRegex(ValueError, "numeric constant"):
                        JSON.parse(document)

    def test_invalid_input_type(self):
        for value in (None, 1, [], {}):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    JSON.parse(value)


class ObjectAccessTests(unittest.TestCase):
    def test_dictionary_method_names_are_available_as_json_properties(self):
        obj = JSON.parse(
            '{"items": [{"value": 3}], "keys": "stored keys", '
            '"values": false, "get": null, "update": 0}'
        )

        self.assertEqual(obj.items[0].value, 3)
        self.assertEqual(obj.keys, "stored keys")
        self.assertIs(obj.values, False)
        self.assertIsNone(obj.get)
        self.assertEqual(obj.update, 0)
        self.assertEqual(dict.get(obj, "keys"), "stored keys")
        self.assertEqual(
            set(dict.keys(obj)), {"items", "keys", "values", "get", "update"}
        )
        self.assertEqual(dict(dict.items(obj)), obj)

    def test_dictionary_methods_work_when_not_shadowed(self):
        obj = JSON.parse('{"value": 3}')

        self.assertEqual(list(obj.items()), [("value", 3)])
        self.assertEqual(obj.get("missing", 7), 7)
        self.assertEqual(list(obj.keys()), ["value"])

    def test_arbitrary_keys_support_bracket_access(self):
        obj = JSON.parse(
            '{"display-name": {"value": 3}, "with space": 2, '
            '"class": "stored class", "": "empty", "0": "zero"}'
        )

        self.assertEqual(obj["display-name"].value, 3)
        self.assertEqual(obj["with space"], 2)
        self.assertEqual(obj["class"], "stored class")
        self.assertEqual(obj[""], "empty")
        self.assertEqual(obj["0"], "zero")

    def test_single_underscore_keys_support_attribute_access(self):
        self.assertEqual(JSON.parse('{"_value": 3}')._value, 3)

    def test_special_python_attributes_are_preserved(self):
        obj = JSON.parse(
            '{"__class__": "stored class", "__dict__": "stored dictionary", '
            '"__getattribute__": "stored method"}'
        )

        self.assertIs(obj.__class__, JSON.JSONObject)
        self.assertEqual(obj["__class__"], "stored class")
        self.assertEqual(obj["__dict__"], "stored dictionary")
        self.assertTrue(callable(obj.__getattribute__))
        self.assertEqual(obj["__getattribute__"], "stored method")

    def test_missing_attribute_and_key_raise_distinct_errors(self):
        obj = JSON.parse("{}")

        with self.assertRaises(AttributeError):
            _ = obj.missing
        with self.assertRaises(KeyError):
            _ = obj["missing"]
        self.assertFalse(hasattr(obj, "missing"))
        self.assertEqual(getattr(obj, "missing", "fallback"), "fallback")

    def test_out_of_range_index_raises_index_error(self):
        with self.assertRaises(IndexError):
            _ = JSON.parse("[]")[0]

    def test_attribute_assignment_and_deletion_change_dictionary(self):
        obj = JSON.parse('{"profile": {"name": "Ada"}}')

        obj.profile.name = "Grace"
        self.assertEqual(obj["profile"]["name"], "Grace")
        obj.profile.active = True
        self.assertIs(obj.profile["active"], True)
        del obj.profile.active
        self.assertNotIn("active", obj.profile)
        with self.assertRaises(AttributeError):
            del obj.profile.active

    def test_special_attribute_mutation_requires_brackets(self):
        obj = JSON.parse('{"__class__": "stored class"}')

        with self.assertRaises(AttributeError):
            obj.__class__ = "other"
        with self.assertRaises(AttributeError):
            del obj.__class__
        obj["__class__"] = "other"
        self.assertEqual(obj["__class__"], "other")
        del obj["__class__"]
        self.assertIs(obj.__class__, JSON.JSONObject)

    def test_new_values_retain_their_python_types(self):
        obj = JSON.parse("{}")
        plain = {"value": 3}

        obj.new = plain
        self.assertIs(obj.new, plain)
        self.assertIs(type(obj.new), dict)
        self.assertEqual(obj.new["value"], 3)
        obj.parsed = JSON.parse('{"value": 4}')
        self.assertEqual(obj.parsed.value, 4)


class SerializationTests(unittest.TestCase):
    def test_round_trip_preserves_values_and_attribute_access(self):
        obj = JSON.parse('{"items": [{"key": {"value": 3}}], "active": true}')

        restored = JSON.parse(JSON.stringify(obj))
        self.assertEqual(restored, obj)
        self.assertEqual(restored.items[0].key.value, 3)
        self.assertIs(restored.active, True)

    def test_standard_json_remains_usable_alongside_package(self):
        plain = json.loads('{"value": {"nested": 3}}')

        self.assertIs(type(plain), dict)
        obj = JSON.parse(json.dumps(plain))
        self.assertEqual(obj.value.nested, 3)
        self.assertEqual(json.loads(json.dumps(obj)), plain)

    def test_nested_method_collisions_serialize_with_formatting(self):
        obj = JSON.parse(
            '{"items": [{"items": {"value": 3}, "keys": 7}]}'
        )

        for indent in (None, 2):
            with self.subTest(indent=indent):
                text = JSON.stringify(obj, indent=indent)
                self.assertEqual(json.loads(text), obj)
                self.assertEqual(JSON.parse(text).items[0].items.value, 3)

    def test_plain_containers_can_contain_parsed_objects(self):
        obj = JSON.parse('{"items": [{"value": 3}]}')
        container = {"objects": (obj, obj)}

        result = JSON.parse(JSON.stringify(container))
        self.assertEqual(result.objects[0].items[0].value, 3)
        self.assertEqual(result.objects[1], obj)

    def test_dumps_alias_and_formatting_options(self):
        self.assertIs(JSON.dumps, JSON.stringify)
        value = {"name": "雪"}

        self.assertEqual(JSON.dumps(value), json.dumps(value, allow_nan=False))
        self.assertEqual(
            JSON.stringify(value, indent=2, ensure_ascii=False),
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False),
        )

    def test_scalar_serialization(self):
        for value in (None, True, False, 0, 3.5, "hello"):
            with self.subTest(value=value):
                self.assertEqual(JSON.parse(JSON.stringify(value)), value)

    def test_non_finite_numbers_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            for document in (value, {"values": [value]}):
                with self.subTest(document=document):
                    with self.assertRaises(ValueError):
                        JSON.stringify(document)

    def test_unsupported_value_type(self):
        with self.assertRaises(TypeError):
            JSON.stringify(object())

    def test_circular_container_is_rejected(self):
        value = JSON.parse("{}")
        value.self = value

        with self.assertRaisesRegex(ValueError, "Circular reference"):
            JSON.stringify(value)

    def test_cycle_through_array_is_rejected(self):
        value = JSON.parse('{"items": []}')
        value.items.append(value)

        with self.assertRaisesRegex(ValueError, "Circular reference"):
            JSON.stringify(value)


if __name__ == "__main__":
    unittest.main()
