"""
A set of utility functions for chainz.

These help with common tasks like reading a file, searching a directory, etc.
"""


def counter(callback):
    """Will count the items that pass by, returning the count to the callback.

    >>> def log(ct):
    >>>     print('Count %d' % ct)
    >>> Chain(xrange(4)).counter(log)\
    >>>     .filter(lambda x: x % 2 == 0).counter(log)\
    >>>     .sink()
    Count 4
    Count 2
    """
    def _counter(in_iterator):
        count = 0
        for x in in_iterator:
            count += 1
            yield x
        callback(count)

    return _counter


def read_file_lines(filepath):
    """Iterates over a file, line by line.

    This generator will yield each line in turn, without the linebreak.
    """
    with open(filepath, 'r') as f:
        for line in f:
            # FIXME: Do more general line ending test.
            if line[-1] == '\n':
                line = line[:-1]
            yield line


def read_jsonl_file(filepath):
    """Iterates over a jsonl file, yielding the JSON objects."""
    import json
    with open(filepath, 'r') as f:
        for line in f:
            yield json.loads(line)


def read_csv_file(filepath, dialect=None):
    """Iterates over a csv file, yielding each line as a tuple.

    The dialect argument is supplied to the csv reader.
    """
    import csv
    with open(filepath, 'r') as f:
        reader = csv.reader(f, dialect=dialect)
        for obj in reader:
            yield obj


def read_csv_dict_file(filepath, dialect=None):
    """Iterates over a csv file, yielding each line as a dict.

    This uses csv.DictReader, so the file should be in a form appropriate to
    that. The dialect argument is supplied to the csv reader.
    """
    import csv
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, dialect=dialect)
        for obj in reader:
            yield obj


def walk_files(root_dir):
    """Iterates under all the files under root_dir, yielding their filepath."""
    import os
    for base_dir, dirs, filenames in os.walk(root_dir):
        for filename in filenames:
            yield os.path.join(base_dir, filename)


def walk_leaf_dirs(root_dir):
    """Yield the paths of the leaf directories under root_dir.

    Leaf directories are those dirs that don't have any subdirectories.
    """
    import os
    for base_dir, dirs, filenames in os.walk(root_dir):
        print 'in %s found dirs %s' % (base_dir, dirs)
        if len(dirs) == 0:
            yield base_dir


def write_lines_to_filepath(filepath, append=False):
    """A transform that writes the incoming objects, one per line, to
    the filepath.

    Use like chain.transform(transform_write_lines_to_filepath(the_filepath))
    If append == True, append to the file instead of overwriting it.
    """
    mode = 'a' if append else 'w'

    def write_lines_to_filepath(in_iterator):
        with open(filepath, mode) as output:
            for x in in_iterator:
                output.write(x + '\n')
                yield x

    return write_lines_to_filepath


def write_json_lines_to_filepath(filepath, append=False):
    """A transform that writes the incoming objects as JSON objects, one per
    line, to the filepath.

    Use like chain.transform(transform_write_json_lines_to_filepath(the_filepath))
    If append == True, append to the file instead of overwriting it.
    """
    import json
    mode = 'a' if append else 'w'

    def write_json_lines_to_filepath(in_iterator):
        with open(filepath, mode) as output:
            for x in in_iterator:
                output.write(json.dumps(x) + '\n')
                yield x

    return write_json_lines_to_filepath
