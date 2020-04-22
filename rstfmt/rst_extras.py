"""
This module handles adding constructs to the reST parser in a way that makes sense for rstfmt.
Nonstandard directives and roles are inserted into the tree unparsed (wrapped in custom node classes
defined here) so we can format them the way they came in without without caring about what they
would normally expand to.
"""

from typing import Any, Dict, Iterator, Optional, Type, TypeVar

import docutils
import sphinx.directives
import sphinx.ext.autodoc.directive
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives import parts
from sphinx.ext import autodoc


T = TypeVar("T")


_new_nodes = []


def _new_node(cls: Type[docutils.nodes.Element]) -> Type[docutils.nodes.Element]:
    _new_nodes.append(cls)
    return cls


@_new_node
class directive(docutils.nodes.Element):
    pass


@_new_node
class role(docutils.nodes.Element):
    def __init__(self, rawtext: str, escaped_text: str, **options: Any) -> None:
        super().__init__(rawtext, escaped_text=escaped_text, options=options)


def _add_directive(
    name: str, cls: Type[docutils.parsers.rst.Directive], *, raw: bool = True,
) -> None:
    # We create a new class inheriting from the given directive class to automatically pick up the
    # argument counts and most of the other attributes that define how the directive is parsed, so
    # parsing can happen as normal. The things we change are:
    #
    # - Relax the option spec so an incorrect name doesn't stop formatting and every option comes
    #   through unchanged.
    # - Override the run method to just stick the directive into the tree.
    # - Add a `raw` attribute to inform formatting later on.
    namespace = {
        "option_spec": autodoc.directive.DummyOptionSpec(),
        "run": lambda self: [directive(directive=self)],
        "raw": raw,
    }
    directives.register_directive(name, type("rstfmt_" + cls.__name__, (cls,), namespace))


def _subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    for c in cls.__subclasses__():
        yield c
        yield from _subclasses(c)


def register() -> None:
    for r in ["class", "download", "func", "ref", "superscript"]:
        roles.register_generic_role(r, role)

    # Do the magic necessary to allow Docutils visitors to work with our new node subclasses.
    docutils.nodes._add_node_class_names([cls.__name__ for cls in _new_nodes])

    # `list-table` directives are parsed into table nodes by default and could be formatted as such,
    # but that's vulnerable to producing malformed tables when the given column widths are too
    # small.
    _add_directive("list-table", directives.tables.ListTable, raw=False)

    _add_directive("contents", directives.parts.Contents)
    _add_directive("include", directives.misc.Include)
    _add_directive("toctree", sphinx.directives.other.TocTree)

    for d in set(_subclasses(autodoc.Documenter)):
        if d.objtype != "object":
            _add_directive("auto" + d.objtype, autodoc.directive.AutodocDirective)

    try:
        import sphinxarg.ext
    except ImportError:
        pass
    else:
        _add_directive("argparse", sphinxarg.ext.ArgParseDirective)
