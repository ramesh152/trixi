import zipfile

import os.path
import re
import sys
from pip.operations import freeze


class SourcePacker(object):
    """
    Inspired by https://github.com/IDSIA/sacred
    """

    @staticmethod
    def join_paths(*parts):
        """Join different parts together to a valid dotted path."""
        return '.'.join(str(p).strip('.') for p in parts if p)

    @staticmethod
    def iter_prefixes(path):
        """
        Iterate through all (non-empty) prefixes of a dotted path.
        Example:
        >>> list(iter_prefixes('foo.bar.baz'))
        ['foo', 'foo.bar', 'foo.bar.baz']
        """
        split_path = path.split('.')
        for i in range(1, len(split_path) + 1):
            yield SourcePacker.join_paths(*split_path[:i])

    @staticmethod
    def create_source_or_dep(mod, sources):
        filename = ''
        if mod is not None and hasattr(mod, '__file__'):
            filename = os.path.abspath(mod.__file__)

        ### To source or dependency
        if filename and filename not in sources and SourcePacker.is_source(filename):
            sources.add(filename)

    @staticmethod
    def is_source(filename):
        if ".virtualenvs" in filename or "site-packages" in filename or re.search("python[0-9]\.[0-9]", filename) is not \
                None:
            return False
        else:
            return True

    @staticmethod
    def gather_sources_and_dependencies(globs):
        py_str = "python {}".format(sys.version)
        dependencies = list(freeze.freeze())

        filename = globs.get('__file__')

        if filename is None:
            sources = set()
        else:
            sources = set()
            sources.add(filename)
        for glob in globs.values():
            if isinstance(glob, type(sys)):
                mod_path = glob.__name__
            elif hasattr(glob, '__module__'):
                mod_path = glob.__module__
            else:
                continue

            if not mod_path:
                continue

            for modname in SourcePacker.iter_prefixes(mod_path):
                mod = sys.modules.get(modname)
                SourcePacker.create_source_or_dep(mod, sources)

        return py_str, sources, dependencies

    @staticmethod
    def zip_sources(globs, filename):

        py_str, sources, dependencies = SourcePacker.gather_sources_and_dependencies(globs=globs)

        with zipfile.ZipFile(filename, mode='w') as zf:
            for source in sources:
                zf.write(source)

            zf.writestr("python_version.txt", py_str)
            dep_str = "\n".join(dependencies)
            zf.writestr("modules.txt", dep_str)
