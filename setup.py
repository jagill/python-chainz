from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(name='chainz',
      version='0.11',
      description='Lightweight chaining functional methods for iterables',
      long_description=readme(),
      keywords='iterable generators functional map filter reduce',
      url='http://github.com/jagill/python-chainz',
      author='James Gill',
      author_email='jamesagill@gmail.com',
      license='MIT',
      packages=['chainz'],
      test_suite='nose.collector',
      tests_require=['nose'],
      include_package_data=True,
      zip_safe=False)
