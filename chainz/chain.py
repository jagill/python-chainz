from itertools import islice, tee
from functools import partial

# Python3 compatibility
try:
  basestring
except NameError:
  basestring = str


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
        self.iter = None
        self._on_error = None
        self._skip = {}  # Unique, non-comparable element

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        if self.iter is None:
            self.iter = iter(self.iterable)
        return self.iter

    def next(self):
        """x.next() -> the next value, or raise StopIteration"""
        return next(iter(self))

    def __next__(self):
        """x.__next__() -> the next value, or raise StopIteration"""
        return next(iter(self))

    def _wrap_iterable(self, f, iterable):
        for x in iterable:
            try:
                out = f(x)
                if out is not self._skip:
                    yield out
            except Exception as e:
                if self._on_error is None:
                    raise
                self._on_error(e, x)

    def _wrap_iterable_with_gen(self, gen, iterable):
        for x in iterable:
            try:
                for out in gen(x):
                    if out is not self._skip:
                        yield out
            except Exception as e:
                if self._on_error is None:
                    raise
                self._on_error(e, x)

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
    def map(self, f, **kwargs):
        """Map the iterator through f.

        Any kwargs passed will be passed to f.
        """
        if kwargs is not None and len(kwargs) > 0:
            f = partial(f, **kwargs)

        self.iterable = self._wrap_iterable(f, self.iterable)
        return self

    def map_key(self, key, f, **kwargs):
        """Map the value of a key through f.

        If key is a tuple or list, apply all values through the same f.
        Any kwargs passed will be passed to f.
        """
        if isinstance(key, basestring):
            key = (key,)

        if kwargs is not None and len(kwargs) > 0:
            f = partial(f, **kwargs)

        def fn(obj):
            for k in key:
                obj[k] = f(obj[k])
            return obj

        self.iterable = self._wrap_iterable(fn, self.iterable)
        return self

    def filter(self, f, **kwargs):
        """Filter the iterator through f.

        Only elements x such that f(x) is Truthy will pass through, the others
        will be dropped.
        Any kwargs passed will be passed to f.
        """
        if kwargs is not None and len(kwargs) > 0:
            f = partial(f, **kwargs)

        def filter_f(x):
            if f(x):
                return x
            return self._skip
        self.iterable = self._wrap_iterable(filter_f, self.iterable)
        return self

    def omit(self, f, **kwargs):
        """Filter the iterator through f.

        Only elements x such that f(x) is Falsy will pass through, the others
        will be dropped.
        Any kwargs passed will be passed to f.
        """
        if kwargs is not None and len(kwargs) > 0:
            f = partial(f, **kwargs)

        def omit_f(x):
            if not f(x):
                return x
            return self._skip
        self.iterable = self._wrap_iterable(omit_f, self.iterable)
        return self

    def do(self, f, **kwargs):
        """Pass all elements through f.

        Unlike for_each, this is not a sink and does not consume the iteratable;
        it creates a new iterable that lazily applies f to each element.
        Note that f may modify the element.  The return value of f is ignored.
        Any kwargs passed will be passed to f.
        """
        if kwargs is not None and len(kwargs) > 0:
            f = partial(f, **kwargs)

        def do_f(x):
            f(x)
            return x
        self.iterable = self._wrap_iterable(do_f, self.iterable)
        return self

    # KEY OPERATIONS
    def set_key(self, key, value, **kwargs):
        """Set a key `key` with value `value` to each object.

        If `value` is a function, call it on the object and use that value
        instead.
        Any kwargs passed will be passed to f.

        Each object must implement dict methods, particularly `__setitem__`.
        """
        if not hasattr(value, '__call__'):
            value_fn = lambda x: value
        else:
            if len(kwargs) > 0:
                value_fn = partial(value, **kwargs)
            else:
                value_fn = value

        def do_f(x):
            x[key] = value_fn(x)
            return x
        self.iterable = self._wrap_iterable(do_f, self.iterable)
        return self

    def drop_key(self, key):
        """Drop the key `key` from each object.

        Each object must implement dict methods, particularly `__delitem__`.
        """
        def do_f(x):
            del x[key]
            return x
        self.iterable = self._wrap_iterable(do_f, self.iterable)
        return self

    def rename_key(self, old_key, new_key, strict=True):
        """Rename old_key to new_key.

        If strict=True, throw an error if the object does not have old_key.
        If strict=False, ignore such objects.
        """
        def rename_key(x):
            try:
                x[new_key] = x.pop(old_key)
            except KeyError:
                if strict:
                    raise
            return x
        self.iterable = self._wrap_iterable(rename_key, self.iterable)
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

        def keep_keys(x):
            new = {}
            for k in keys:
                if k in x:
                    new[k] = x[k]
            return new

        self.iterable = self._wrap_iterable(keep_keys, self.iterable)
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
    def mapcat(self, gen):
        """Applies a generator gen to each item, yielding the results sequentially.

        Example:
        def gen(x):
            for letter in ['a', 'b']:
                yield '%s%s' % (x, letter)
        chain = Chain(xrange(3)).mapcat(gen)
        print list(chain)
        # ['0a', '0b', '1a', '1b', '2a', '2b']
        """
        self.iterable = self._wrap_iterable_with_gen(gen, self.iterable)
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
                except TypeError:
                    if strict:
                        raise
                    else:
                        yield x

        self.iterable = self._wrap_iterable_with_gen(flatten_gen, self.iterable)
        return self

    def transform(self, trans, **kwargs):
        """Pass the iterator through the transform f.

        This is a lower-level method.  A transform does not get each individual
        object, rather it gets the original iterator.  It must return an
        iterator.  For example,
        def f(in_iterator):
            with open('filename', 'w') as output:
                for x in in_iterator:
                    output.write(x)
                    yield x

        This will keep the output open throughout the iteration.
        Note that the transform is responsible for calling on_error, if
        appropriate.  Please see the examples in the above functions.

        Any kwargs passed will be passed to trans.
        """
        if len(kwargs) > 0:
            trans = partial(trans, **kwargs)

        self.iterable = trans(self.iterable)
        return self

    # Sinks
    def sink(self):
        """Consume the iterable; do nothing additional with the elements.

        Note that this is a sink; it entirely consumes the iterable.
        """
        for x in self.iterable:
            pass

    def reduce(self, f, first=None):
        """Reduce the iterable by f, with optional first value.

        Supplying first=None is the same as not supplying it.  If it is not
        supplied, use the first value f the iterable as the first value.

        Note that this is a sink; it entirely consumes the iterable.
        """
        if first is not None:
            result = first
        else:
            try:
                result = next(self)
            except StopIteration:
                result = None

        for x in self.iterable:
            try:
                result = f(result, x)
            except Exception as e:
                if self._on_error is None:
                    raise
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
        def _for_each(res, x):
            f(x)

        self.reduce(_for_each, 0)

    # Multiple chain operations
    def copy(self):
        """Make a copy of this chain.

        This chain and the copy can be iterated independently.
        """
        self.iterable, it = tee(self.iterable, 2)
        return Chain(it)

    def join_on_key(self, key, other):
        """Merge other iterable into this chain, on shared key.

        This assumes that key is unique in both iterables.
        It will yield an object merging the object for the key
        from each iterable.  It will yield in the order that
        it completes each.  It will drop all objects that
        don't have a mate.

        Note that this stores the unpaired objects, so it can
        potentially use up a lot of memory.  It will consume
        from each queue until it has a match, so in the worst
        case (no matching objects) it will consume and store
        in memory each realized iterable.
        """
        self.iterable = join_on_key(key, self.iterable, other)
        return self


def join_on_key(key, a, b):
    """Join two iterables on a shared key.

    This will merge the object in a and the object in b that have
    the same value for key.  It will drop an unpaired objects.  It
    assumes the values for key are unique in each of a and b.
    For keys shared between a and b, the b value will be used.
    """
    a_store = {}
    b_store = {}
    a_iter = a.__iter__()
    b_iter = b.__iter__()
    a_active = True
    b_active = True
    while a_active or b_active:
        if a_active:
            try:
                x = next(a_iter)
                x = dict(x)  # Copy so as not to modify x
                if x[key] in b_store:
                    y = b_store.pop(x[key])
                    x.update(y)
                    yield x
                else:
                    a_store[x[key]] = x
            except StopIteration:
                a_active = False

        if b_active:
            try:
                y = next(b_iter)
                if y[key] in a_store:
                    x = a_store.pop(y[key])
                    x.update(y)
                    yield x
                else:
                    b_store[y[key]] = y
            except StopIteration:
                b_active = False
