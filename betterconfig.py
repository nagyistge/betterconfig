#!/usr/bin/python
'''
============
betterconfig
============

betterconfig provides a more convenient and extensible configuration language,
built on python's builtin ConfigParser format.

Type Coercion Boilerplate Sucks
-------------------------------

ConfigParser, like many config languages, treats all values as strings,
meaning that when you have configs like this:

::

    [config]
    foo = 1
    bar = a,list,of,strings
    baz = just a plain old string

you end up with boilerplate that looks like this:

::

    from ConfigParser import ConfigParser
    MAP = {
        'foo': int,
        'bar': lambda x: x.split(','),
        'baz': str,
    }
    c = ConfigParser()
    c.read('./foo.cfg')
    config = {k:MAP[k](v) for k,v in c.items('config')}

Don't you really wish you could just do this:

::

    [config]
    foo = 1
    bar = ['a', 'list', 'of', 'strings']
    baz = "just a plain old string"

and drop the map?

::

    import betterconfig
    config = betterconfig.load('./foo.cfg')['config']

betterconfig supports all literal types supported by ast.literal_eval_:
strings, numbers, tuples, lists, dicts, booleans, and None.

.. _ast.literal_eval: http://docs.python.org/2/library/ast.html#ast.literal_eval

More Flexibility in Config, Means Less Config by Module
-------------------------------------------------------

We wanted a config language that was as easy to use as a settings module in
django or flask (and nearly as extensible), but less magical to initialize,
and slightly safer than something like this:

::

    import importlib
    settings = importlib.import_module('settings')

So we want a config that can do stuff like this:

::

    top_level  = 'variables defined outside of sections'
    include    = ['./include.cfg', 'include.d/*.cfg']

    [section]
    namespaced = True

And we don't want to have to iterate sections or items, we really just want to
load it into a dict:

::

    import betterconfig
    settings = betterconfig.load('./fancy.cfg')

And if you're really in love with `.' notation, you can always do something
silly like make a module `settings.py' that does something magical like:

::

    import betterconfig
    globals().update(betterconfig.load('./fancy.cfg'))

Authors
-------

| Matthew Story <matt.story@axial.net>
| Inspired By: http://stackoverflow.com/a/6209146
| Inspired By: http://stackoverflow.com/a/2819788

'''
import os
import ast
import glob
from ConfigParser import ConfigParser, MissingSectionHeaderError

######## BEGIN SECTIONLESS HACKS
class _Sectionless(object):
    '''Hack for sectionless config'''
    def __init__(self, file_, sect):
        self.__was_open, self.__file = self.__open(file_)
        self.__secthead = '[{}]'.format(sect)

    def __getattr__(self, attr):
        return getattr(self.__file, attr)

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        if not self.__was_open:
            self.__file.close()

    def __open(self, file_):
        # this is all we really care about ... quack, quack
        if hasattr(file_, 'readline'):
            return True, file_
        return False, open(file_, 'r')

    def readline(self):
        if self.__secthead:
            try:
                return self.__secthead
            finally:
                self.__secthead = None

        return self.__file.readline()
######## END SECTIONLESS HACKS

def _id_and_dir(cfg_file):
    '''Return dirname and inode of open filish'''
    dir_name = os.path.dirname(getattr(cfg_file, 'name', ''))
    try:
        return os.fstat(cfg_file.fileno()).st_ino, dir_name
    except AttributeError:
        return None, dir_name

def load(*cfgs, **kwargs):
    '''Load a betterconfig config file into a python dict and return.'''
    include = kwargs.pop('include', 'include')
    default = kwargs.pop('default', '_')
    seen = kwargs.pop('seen', set())
    if kwargs:
        raise TypeError('{} is an invalid keyword argument'\
                        'for this function'.format(kwargs.keys()[0]))

    compiled_config = {}
    for cfg in cfgs:
        includes = []
        with _Sectionless(cfg, default) as cfg_file:
            # prevent infinite include recursion
            id_, cfg_dir = _id_and_dir(cfg_file)
            if id_ in seen:
                continue
            elif id_ is not None:
                seen.add(id_)

            parser = ConfigParser()
            parser.readfp(cfg_file)

            for sect in parser.sections():
                sect_config = compiled_config
                if sect != default:
                    sect_config = compiled_config.setdefault(sect, {})

                for key,val in parser.items(sect):
                    val = ast.literal_eval(val)
                    if sect == default and key == include:
                        val = [val] if isinstance(val, basestring) else val
                        for glob_includes in val:
                            # expand and sort to support 0001-style convention
                            glob_includes = glob.glob(os.path.join(cfg_dir, glob_includes))
                            glob_includes.sort()
                            includes.extend(glob_includes)
                    else:
                        sect_config[key] = val

        # after we've finished one file, overlay any includes
        if includes:
            compiled_config.update(load(*includes, default=default, seen=seen,
                                        include=include))

    return compiled_config

__all__ = ['load']

if __name__ == '__main__':
    import sys
    import pprint
    pprint.pprint(load(*(sys.argv[1:] or [sys.stdin])))
