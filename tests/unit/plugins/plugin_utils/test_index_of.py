# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function


__metaclass__ = type

import re

from unittest import TestCase

from jinja2 import Environment

from ansible_collections.ansible.utils.plugins.plugin_utils.index_of import index_of


def jinja_match(value, pattern):
    return re.match(pattern, value) is not None


def jinja_search(value, pattern):
    return re.search(pattern, value) is not None


class TestIndexOfFilter(TestCase):
    def setUp(self):
        env = Environment()
        env.tests["match"] = jinja_match
        env.tests["search"] = jinja_search
        self._tests = env.tests

    def test_fail_no_qualfier(self):
        obj, test, value = [1, 2], "@@", 1
        with self.assertRaises(Exception) as exc:
            index_of(obj, test, value, tests=self._tests)
        self.assertIn("the test '@@' was not found", str(exc.exception))
        obj, test, value, key = [{"a": 1}], "@@", 1, "a"
        with self.assertRaises(Exception) as exc:
            index_of(obj, test, value, key, tests=self._tests)
        self.assertIn("the test '@@' was not found", str(exc.exception))

    def test_fail_mixed_list(self):
        obj, test, value, key = [{"a": "b"}, True, 1, "a"], "==", "b", "a"
        with self.assertRaises(Exception) as exc:
            index_of(obj, test, value, key, tests=self._tests)
        self.assertIn("required to be dictionaries", str(exc.exception))

    def test_fail_key_not_valid(self):
        obj, test, value, key = [{"a": "b"}], "==", "b", [1, 2]
        with self.assertRaises(Exception) as exc:
            index_of(obj, test, value, key, tests=self._tests)
        self.assertIn("Unknown key type", str(exc.exception))

    def test_fail_on_missing(self):
        obj, test, value, key = [{"a": True}, {"c": False}], "==", True, "a"
        with self.assertRaises(Exception) as exc:
            index_of(obj, test, value, key, fail_on_missing=True, tests=self._tests)
        self.assertIn("'a' was not found", str(exc.exception))

    def test_just_test(self):
        """Limit to jinja < 2.11 tests"""
        objs = [
            # ([True], "true", 0),
            # ([False], "not false", []),
            # ([False, 5], "boolean", 0),
            # ([0, False], "false", 1),
            ([3, 4], "not even", 0),
            ([3, 4], "even", 1),
            ([3, 3], "even", []),
            ([3, 3, 3, 4], "odd", [0, 1, 2]),
            # ([3.3, 3.4], "float", [0, 1]),
        ]
        for entry in objs:
            obj, test, answer = entry
            result = index_of(obj, test, tests=self._tests)
            expected = answer
            self.assertEqual(result, expected)

    def test_simple_lists(self):
        objs = [
            ([1, 2, 3], "==", 2, 1),
            (["a", "b", "c"], "eq", "c", 2),
            ([True, False, 0, 1], "equalto", False, [1, 2]),
            ([True, False, "0", "1"], "==", False, 1),
            ([True, False, "", "1"], "==", False, 1),
            ([True, False, "", "1"], "in", False, 1),
            ([True, False, "", "1", "a"], "in", [False, "1"], [1, 3]),
            ([1, 2, 3, "a", "b", "c"], "!=", "c", [0, 1, 2, 3, 4]),
            ([1, 2, 3], "!<", 3, 2),
        ]
        for entry in objs:
            obj, test, value, answer = entry
            result = index_of(obj, test, value, tests=self._tests)
            expected = answer
            self.assertEqual(result, expected)

    def test_simple_dict(self):
        objs = [
            ([{"a": 1}], "==", 1, "a", 0),
            ([{"a": 1}], "==", 1, "b", []),
            ([{"a": 1}], "==", 2, "a", []),
            (
                [{"a": 1}, {"a": 1}, {"a": 1}, {"a": 2}],
                "==",
                1,
                "a",
                [0, 1, 2],
            ),
            (
                [{"a": "abc"}, {"a": "def"}, {"a": "ghi"}, {"a": "jkl"}],
                "match",
                "^a",
                "a",
                0,
            ),
            (
                [{"a": "abc"}, {"a": "def"}, {"a": "ghi"}, {"a": "jkl"}],
                "search",
                "e",
                "a",
                1,
            ),
        ]
        for entry in objs:
            obj, test, value, key, answer = entry
            result = index_of(obj, test, value, key, tests=self._tests)
            self.assertEqual(result, answer)
