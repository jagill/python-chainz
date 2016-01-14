from chainz import Chain
import unittest
import operator


class TestChain(unittest.TestCase):
    def test_constructor(self):
        a = xrange(3)
        b = Chain(a)
        self.assertEqual(list(b), [0, 1, 2])

    def test_iter(self):
        a = Chain(xrange(2))
        it = a.__iter__()
        self.assertEqual(it.next(), 0)
        self.assertEqual(it.next(), 1)
        try:
            it.next()
        except StopIteration:
            pass
        else:
            self.fail()

    # def test_next(self):
    #     a = Chain(xrange(2))
    #     self.assertEqual(a.next(), 0)
    #     self.assertEqual(a.next(), 1)
    #     try:
    #         a.next()
    #     except StopIteration:
    #         pass
    #     else:
    #         self.fail()
    #
    # MAPPING TYPES
    def test_map(self):
        a = xrange(4)
        b = Chain(a).map(lambda x: 2*x)
        self.assertEqual(list(b), [0, 2, 4, 6])

    def test_map_error(self):
        a = xrange(4)
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def f(x):
            if x == 1:
                raise e
            return 2*x

        b = Chain(a)\
            .on_error(err_f)\
            .map(f)
        self.assertEqual(list(b), [0, 4, 6])

    def test_map_error_no_error_fn(self):
        def f(x):
            if x == 1:
                raise Exception('bad')
            return 2*x

        b = Chain(xrange(4)).map(f)
        with self.assertRaises(Exception):
            list(b)

    def test_map_key(self):
        def make_obj(x):
            return dict(k=x)

        b = Chain(xrange(3)).map(make_obj).map_key('k', lambda x: x*2)
        self.assertEqual(list(b), [
            {'k': 0},
            {'k': 2},
            {'k': 4},
        ])

    def test_filter(self):
        a = xrange(4)
        b = Chain(a).filter(lambda x: x % 2)
        self.assertEqual(list(b), [1, 3])

    def test_filter_error(self):
        a = xrange(4)
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def f(x):
            if x == 1:
                raise e
            return x % 2 == 1

        b = Chain(a)\
            .on_error(err_f)\
            .filter(f)
        self.assertEqual(list(b), [3])

    def test_omit(self):
        a = xrange(4)
        b = Chain(a).omit(lambda x: x % 2)
        self.assertEqual(list(b), [0, 2])

    def test_do(self):
        res = []

        def f(x):
            res.append(x)
        list(Chain(xrange(3)).do(f))
        self.assertEqual(res, [0, 1, 2])

    def test_do_error(self):
        e = Exception('bad')
        res = []

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def f(x):
            if x == 1:
                raise e
            res.append(x)
        list(Chain(xrange(3)).do(f).on_error(err_f))
        self.assertEqual(res, [0, 2])

    def test_set_key(self):
        objs = [{}, {'a': 'x'}, {'b': 'y'}]
        res = list(Chain(objs).set_key('a', 'z'))
        desired_result = [{'a': 'z'}, {'a': 'z'}, {'a': 'z', 'b': 'y'}]
        self.assertEqual(res, desired_result)

    def test_set_key_fn(self):
        objs = [{'a': 4}, {'a': 2}, {'a': 1}]
        res = list(Chain(objs).set_key('b', lambda x: x['a'] + 2))
        desired_result = [
            {'a': 4, 'b': 6},
            {'a': 2, 'b': 4},
            {'a': 1, 'b': 3}
        ]
        self.assertEqual(res, desired_result)

    def test_keep_keys_single(self):
        objs = [
            dict(a=1, b=2),
            dict(a=4, b=5),
        ]
        res = list(Chain(objs).keep_keys('a'))
        desired_result = [{'a': 1}, {'a': 4}]
        self.assertEqual(res, desired_result)

    def test_keep_keys_multiple(self):
        objs = [
            dict(a=1, b=2, c=3),
            dict(a=4, b=5, c=6),
        ]
        res = list(Chain(objs).keep_keys(['a', 'b']))
        desired_result = [{'a': 1, 'b': 2}, {'a': 4, 'b': 5}]
        self.assertEqual(res, desired_result)

    def test_keep_keys_missing(self):
        objs = [
            dict(a=1, b=2),
            dict(a=4, b=5),
        ]
        res = list(Chain(objs).keep_keys(['a', 'c']))
        desired_result = [{'a': 1}, {'a': 4}]
        self.assertEqual(res, desired_result)

    # GENERATOR OPERATIONS
    def test_mapcat(self):
        def gen(x):
            for letter in ['a', 'b']:
                yield '%s%s' % (x, letter)
        b = Chain(xrange(3)).mapcat(gen)
        self.assertEqual(list(b), ['0a', '0b', '1a', '1b', '2a', '2b'])

    def test_mapcat_error(self):
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def gen(x):
            for letter in ['a', 'b']:
                out = '%s%s' % (x, letter)
                if out == '1a':
                    raise e
                else:
                    yield out

        b = Chain(xrange(3)).mapcat(gen).on_error(err_f)
        self.assertEqual(list(b), ['0a', '0b', '2a', '2b'])

    def test_mapcat_error_2(self):
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def gen(x):
            for letter in ['a', 'b']:
                out = '%s%s' % (x, letter)
                if out == '1b':
                    raise e
                else:
                    yield out

        b = Chain(xrange(3)).mapcat(gen).on_error(err_f)
        self.assertEqual(list(b), ['0a', '0b', '1a', '2a', '2b'])

    def test_flatten(self):
        b = Chain(xrange(4)).map(lambda x: xrange(x)).flatten()
        self.assertEqual(list(b), [0, 0, 1, 0, 1, 2])

    def test_flatten_strict(self):
        def err_f(ex, o):
            self.assertIsInstance(ex, TypeError)
            self.assertEqual(o, 2)

        def f(x):
            if x == 2:
                return x
            return xrange(x)

        b = Chain(xrange(4)).on_error(err_f).map(f).flatten()
        self.assertEqual(list(b), [0, 0, 1, 2])

    def test_flatten_not_strict(self):
        def err_f(ex, o):
            self.assertFalse('Should not call this!')

        def f(x):
            if x == 2:
                return x
            return xrange(x)

        b = Chain(xrange(4)).on_error(err_f).map(f).flatten(strict=False)
        self.assertEqual(list(b), [0, 2, 0, 1, 2])

    # CONTROLS
    def test_slice_none(self):
        a = xrange(10)
        b = Chain(a).slice(None)
        self.assertEqual(len(list(b)), len(a))

    def test_slice_end(self):
        a = xrange(10)
        b = Chain(a).slice(4)
        self.assertEqual(list(b), [0, 1, 2, 3])

    def test_slice_beg_end(self):
        a = xrange(10)
        b = Chain(a).slice(2, 6)
        self.assertEqual(list(b), [2, 3, 4, 5])

    def test_slice_beg_end_step(self):
        a = xrange(10)
        b = Chain(a).slice(2, 8, 3)
        self.assertEqual(list(b), [2, 5])

    # SINKS
    def test_sink(self):
        res = []

        def f(x):
            res.append(x)
        Chain(xrange(3)).do(f).sink()
        self.assertEqual(res, [0, 1, 2])

    def test_count(self):
        n = 10**6
        ct = Chain(xrange(n)).count()
        self.assertEqual(ct, n)

    def test_count_composite(self):
        n = 10**6
        ct = Chain(xrange(n)).slice(100, n - 100, 2).count()
        self.assertEqual(ct, (n - 200) / 2)

    def test_reduce(self):
        res = Chain(xrange(4)).reduce(operator.add)
        self.assertEqual(res, 6)

    def test_reduce_first(self):
        res = Chain(xrange(4)).reduce(operator.add, 10)
        self.assertEqual(res, 16)

    def test_reduce_error(self):
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def f(r, x):
            if x == 1:
                raise e
            return r + x

        res = Chain(xrange(4)).on_error(err_f).reduce(f)
        self.assertEqual(res, 5)

    def test_for_each(self):
        res = []

        def f(x):
            res.append(x)
        Chain(xrange(3)).for_each(f)
        self.assertEqual(res, [0, 1, 2])

    def test_for_each_error(self):
        res = []
        e = Exception('bad')

        def err_f(ex, o):
            self.assertEqual(ex, e)
            self.assertEqual(o, 1)

        def f(x):
            if x == 1:
                raise e
            res.append(x)

        Chain(xrange(3)).on_error(err_f).for_each(f)
        self.assertEqual(res, [0, 2])

    # Multiple Chain operations
    def test_copy(self):
        a = Chain(xrange(3))
        b = a.copy()
        a.map(lambda x: 2*x)

        self.assertEqual(list(a), [0, 2, 4])
        self.assertEqual(list(b), [0, 1, 2])

    def test_copy_after_map(self):
        a = Chain(xrange(3)).map(lambda x: 2*x)
        b = a.copy()
        a.map(lambda x: 3*x)

        self.assertEqual(list(a), [0, 6, 12])
        self.assertEqual(list(b), [0, 2, 4])

    def test_merge_on_key(self):
        a = Chain(xrange(4)).map(lambda x: {'a': x, 'b': 'z%d' % x})
        b = Chain(xrange(4)).map(lambda x: {'a': x, 'c': 'y%d' % x})
        a.merge_on_key('a', b)
        desired_result = [
            {'a': 0, 'b': 'z0', 'c': 'y0'},
            {'a': 1, 'b': 'z1', 'c': 'y1'},
            {'a': 2, 'b': 'z2', 'c': 'y2'},
            {'a': 3, 'b': 'z3', 'c': 'y3'},
        ]
        self.assertEqual(list(a), desired_result)

    def test_merge_on_key_phased(self):
        a = Chain(xrange(4)).map(lambda x: {'a': x, 'b': 'z%d' % x})
        b = Chain(xrange(4)).map(lambda x: {'a': 3-x, 'c': 'y%d' % x})
        a.merge_on_key('a', b)
        desired_result = [
            {'a': 0, 'b': 'z0', 'c': 'y3'},
            {'a': 1, 'b': 'z1', 'c': 'y2'},
            {'a': 2, 'b': 'z2', 'c': 'y1'},
            {'a': 3, 'b': 'z3', 'c': 'y0'},
        ]
        actual_result = sorted(list(a), key=lambda o: o['a'])
        self.assertEqual(actual_result, desired_result)
