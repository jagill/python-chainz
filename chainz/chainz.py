from itertools import islice


class Chain:
    """
    A Chain is a lightweight, functional, chaining wrapper around an iterable.

    It provides methods such as `map` or `filter` that act lazily on the
    iterable.  Each of these methods returns the chain object so that the
    methods can be chained (hence the name).  It is similar in functionality
    to itertoolz, but in an order the author finds easier to read, and without
    the ambiguity of whether the iterable, or the other arguments, comes first.

    It also includes "sink" methods, which consume the iterable.  For example,
    `reduce` will reduce the iterable via a supplied binary function, and
    `for_each` will apply a supplied function to each element.

    It bears repeating that all operations are performed lazily.  In fact, if
    no sink method is called, and if the chain is not consumed in some other
    fashion (like you would any other iterable), nothing will actually happen.
    The chain will be un-evaluated, and the iterable will not be consumed.
    """

    def __init__(self, iterable):
        """Create a chain with the supplied iterable."""
        self.iterable = iterable
        self._on_error = None
        self._skip = {}  # Unique, non-comparable element

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        return self.iterable.__iter__()

    def next(self):
        """x.next() -> the next value, or raise StopIteration"""
        return self.iterable.next()

    def _wrap_iterator(self, f):
        def new_it(old_it):
            for x in old_it:
                try:
                    out = f(x)
                    if out is not self._skip:
                        yield out
                except Exception as e:
                    if self._on_error is None:
                        raise e
                    self._on_error(e, x)

        self.iterable = new_it(self.iterable)

    def _wrap_iterator_with_generator(self, gen):
        def new_it(old_it):
            for x in old_it:
                try:
                    for out in gen(x):
                        if out is not self._skip:
                            yield out
                except Exception as e:
                    if self._on_error is None:
                        raise e
                    self._on_error(e, x)

        self.iterable = new_it(self.iterable)

    def on_error(self, f):
        """Sets the error handler for the chain.

        If an exception is thrown by a chained function, use the error function
        instead of terminating the iteration.  After the error is handled,
        continue iteration on the next item.

        If this is never called, an exception will halt iteration and be raised
        normally.  If this is called multiple times, the successive calls will
        replace (not append to) the previous error handler.

        The function f receives two arguments, the thrown exception, and the
        object that caused the exception.  E.g, the function should be of the
        form
        def f(exception, object):
            # do something
        """
        self._on_error = f
        return self

    # Mapping-type operations
    def map(self, f):
        """Map the iterator through f."""
        self._wrap_iterator(f)
        return self

    def map_key(self, key, f):
        """Map the value of a key through f."""
        def fn(obj):
            obj[key] = f(obj[key])
            return obj

        self._wrap_iterator(fn)
        return self

    def filter(self, f):
        """Filter the iterator through f.

        Only elements x such that f(x) is Truthy will pass through, the others
        will be dropped.
        """
        def filter_f(x):
            if f(x):
                return x
            return self._skip
        self._wrap_iterator(filter_f)
        return self

    def omit(self, f):
        """Filter the iterator through f.

        Only elements x such that f(x) is Falsy will pass through, the others
        will be dropped.
        """
        def omit_f(x):
            if not f(x):
                return x
            return self._skip
        self._wrap_iterator(omit_f)
        return self

    def do(self, f):
        """Pass all elements through f.

        Unlike for_each, this is not a sink and does not consume the iteratable;
        it creates a new iterable that lazily applies f to each element.
        Note that f may modify the element.  The return value of f is ignored.
        """
        def do_f(x):
            f(x)
            return x
        self._wrap_iterator(do_f)
        return self

    # KEY OPERATIONS
    def set_key(self, key, value):
        """Set a key `key` with value `value` to each object.

        If `value` is a function, call it on the object and use that value
        instead.

        Each object must implement dict methods, particularly `__setitem__`.
        """
        if not hasattr(value, '__call__'):
            value_fn = lambda x: value
        else:
            value_fn = value

        def do_f(x):
            x[key] = value_fn(x)
            return x
        self._wrap_iterator(do_f)
        return self

    def drop_key(self, key):
        """Drop the key `key` from each object.

        Each object must implement dict methods, particularly `__delitem__`.
        """
        def do_f(x):
            del x[key]
            return x
        self._wrap_iterator(do_f)
        return self

    def keep_keys(self, keys):
        """Keep only the provided keys in each object.

        keys can be a list, tuple, or string.  If the latter, keep only the
        specified key.  Otherwise, keep all the keys in the list/tuple.

        If a key is specified that does not exist in the input object, it is
        not added.

        Note that this creates a new object; it does not modify the old object.
        """
        if isinstance(keys, basestring):
            keys = [keys]

        def do_f(x):
            new = {}
            for k in keys:
                if k in x:
                    new[k] = x[k]
            return new

        self._wrap_iterator(do_f)
        return self

    # Control operations
    def slice(self, *args):
        """Slice the iterator.

        Arguments are the same as for the built-in slice object.  They are
        slice(end): slice first `end` elements
        slice(beg, end, [step]): start slice at `beg`, end at `end`, with step
            `step` if provided.
        """
        self.iterable = islice(self.iterable, *args)
        return self

    # Generator operations
    def map_gen(self, gen):
        """Applies a generator gen to each item, yielding the results sequentially.

        Example:
        def gen(x):
            for letter in ['a', 'b']:
                yield '%s%s' % (x, letter)
        chain = Chain(xrange(3)).map_gen(gen)
        print list(chain)
        # ['0a', '0b', '1a', '1b', '2a', '2b']
        """
        self._wrap_iterator_with_generator(gen)
        return self

    def flatten(self, strict=True):
        """Flattens the iterables in iterable.

        If strict is True, raise an Exception for any non-iterables in iterable.
        If strict is False, pass them through.
        """
        def flatten_gen(x):
                try:
                    for y in x:
                        yield y
                except TypeError as e:
                    if strict:
                        raise e
                    else:
                        yield x

        self._wrap_iterator_with_generator(flatten_gen)
        return self

    # Sinks
    def sink(self):
        """Consume the iterable; do nothing additional with the elements.

        Note that this is a sink; it will entirely consume the iterable.
        """
        for x in self.iterable:
            pass

    def reduce(self, f, first=None):
        """Reduce the iterable by f, with optional first value.

        Supplying first=None is the same as not supplying it.  If it is not
        supplied, use the first value f the iterable as the first value.

        Note that this is a sink; it entirely consumes the iterable.
        """
        result = _start = {}  # Unique, non-comparable element
        if first is not None:
            result = first

        for x in self.iterable:
            if result is _start:
                result = x
                continue
            try:
                result = f(result, x)
            except Exception as e:
                if self._on_error is None:
                    raise e
                self._on_error(e, x)

        return result

    def count(self):
        """Reduce an iterator it to a count.

        Note that this is a sink; it entirely consumes the iterable.
        """
        def _count(x, y):
            return x + 1

        return self.reduce(_count, 0)

    def for_each(self, f):
        """Consume the iterator by applying f to each element.

        The return value of f is ignored.
        Note that this is a sink; it entirely consumes the iterable.
        """
        for x in self.iterable:
            try:
                f(x)
            except Exception as e:
                if self._on_error is None:
                    raise e
                self._on_error(e, x)
