import os
import unittest
import json
import csv
import tempfile
from chainz import Chain, utils

base_dir = os.path.dirname(__file__)


class TestChain(unittest.TestCase):
    def test_counter(self):
        l = []

        def accumulate(count):
            l.append(count)

        Chain(xrange(4))\
            .transform(utils.counter(accumulate))\
            .filter(lambda x: x % 2 == 0)\
            .transform(utils.counter(accumulate))\
            .sink()
        self.assertEqual(l, [4, 2])

    def test_read_file(self):
        filename = os.path.join(base_dir, 'data', 'textdat.txt')
        line_it = utils.read_file(filename)
        self.assertEqual(list(line_it), ['a', 'b', 'c'])

    def test_read_jsonl_file(self):
        filename = os.path.join(base_dir, 'data', 'jsondat.jsonl')
        line_it = utils.read_jsonl_file(filename)
        self.assertEqual(list(line_it), [
            {"a": 1, "b": True},
            {"c": "d", "b": False}
        ])

    def test_read_csv_file(self):
        filename = os.path.join(base_dir, 'data', 'csvdat.csv')
        line_it = utils.read_csv_file(filename)
        self.assertEqual(list(line_it), [
            ['a', 'b', 'c'],
            ['1', '2', '3'],
            ['4', '5', '6']
        ])

    def test_read_csv_dict_file(self):
        filename = os.path.join(base_dir, 'data', 'csvdat.csv')
        line_it = utils.read_csv_dict_file(filename)
        self.assertEqual(list(line_it), [
            {'a': '1', 'b': '2', 'c': '3'},
            {'a': '4', 'b': '5', 'c': '6'},
        ])

    def test_walk_files(self):
        files = []
        root_dir = os.path.join(base_dir, 'data')
        for base, dirs, fns in os.walk(root_dir):
            files += [os.path.join(base, fn) for fn in fns]
        result = list(utils.walk_files(root_dir))
        self.assertEqual(result, files)

    def test_walk_leaf_dirs(self):
        root_dir = os.path.join(base_dir, 'data')
        result = list(utils.walk_leaf_dirs(root_dir))
        self.assertEqual(result, [os.path.join(root_dir, 'subdir')])

    def test_write_file(self):
        data = ['a', 'b', 'c']
        # TODO: Do tempfile.mkstemp stuff
        tempfilepath = tempfile.mktemp()
        transform = utils.write_file(tempfilepath)
        result = list(transform(data))
        self.assertEqual(result, data)
        with open(tempfilepath, 'r') as temp_f:
            self.assertEqual(temp_f.read(), 'a\nb\nc\n')
        # FIXME This probably doesn't remove the file if the assertion fails.
        os.remove(tempfilepath)

    def test_write_file_append(self):
        data = ['a', 'b', 'c']
        tempfilepath = tempfile.mktemp()
        with open(tempfilepath, 'w') as temp_f:
            temp_f.write('zzz\n')
        transform = utils.write_file(tempfilepath, append=True)
        result = list(transform(data))
        self.assertEqual(result, data)
        with open(tempfilepath, 'r') as temp_f:
            self.assertEqual(temp_f.read(), 'zzz\na\nb\nc\n')
        # FIXME This probably doesn't remove the file if the assertion fails.
        os.remove(tempfilepath)

    def test_write_jsonl_file(self):
        # TODO: Do tempfile stuff
        data = [
            {'a': 1, 'b': False},
            {'c': 'd', 'b': False},
        ]
        tempfilepath = tempfile.mktemp()
        transform = utils.write_jsonl_file(tempfilepath)
        result = list(transform(data))
        self.assertEqual(result, data)
        with open(tempfilepath, 'r') as temp_f:
            result_data = [json.loads(x) for x in temp_f]
            self.assertEqual(result_data, data)
        # FIXME This probably doesn't remove the file if the assertion fails.
        os.remove(tempfilepath)

    def test_write_jsonl_file_append(self):
        data = [
            {'a': 1, 'b': False},
            {'c': 'd', 'b': False},
        ]
        extra = {'d': 'e', 'b': True}
        expected_data = [extra] + data
        tempfilepath = tempfile.mktemp()
        with open(tempfilepath, 'w') as temp_f:
            temp_f.write(json.dumps(extra) + '\n')
        transform = utils.write_jsonl_file(tempfilepath, append=True)
        result = list(transform(data))
        self.assertEqual(result, data)
        with open(tempfilepath, 'r') as temp_f:
            result_data = [json.loads(x) for x in temp_f]
            self.assertEqual(result_data, expected_data)
        # FIXME This probably doesn't remove the file if the assertion fails.
        os.remove(tempfilepath)

    def test_write_csv_dict_file(self):
        # TODO: Do tempfile stuff
        data = [
            {'a': '1', 'b': 'abc'},
            {'a': '2', 'b': 'def'},
        ]
        tempfilepath = tempfile.mktemp()
        transform = utils.write_csv_dict_file(tempfilepath, ('a', 'b'))
        result = list(transform(data))
        self.assertEqual(result, data)
        with open(tempfilepath, 'r') as temp_f:
            reader = csv.DictReader(temp_f)
            result_data = list(reader)
            self.assertEqual(result_data, data)
        # FIXME This probably doesn't remove the file if the assertion fails.
        os.remove(tempfilepath)
