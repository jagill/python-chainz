from chainz import Chain
import unittest
from collections import OrderedDict


class TestChainDebug(unittest.TestCase):
    """
    Test the debug functions of Chain.
    """
    def test_simple_count(self):
        c = Chain(xrange(4), debug=True).map(lambda x: x)
        list(c)
        self.assertEqual(c._counts, {'0:map': 4})

    def test_two_counts(self):
        c = Chain(xrange(4), debug=True)\
            .map(lambda x: x)\
            .filter(lambda x: x % 2)
        list(c)
        target_dict = OrderedDict([('0:map', 4), ('1:filter', 2)])
        self.assertEqual(c._counts, target_dict)
