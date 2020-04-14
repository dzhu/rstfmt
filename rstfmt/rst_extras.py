import docutils
import sphinx.directives
import sphinx.ext.autodoc.directive
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives import parts
from sphinx.ext import autodoc

# Handle directives and roles by inserting them into the tree unparsed.


_new_nodes = []


def _new_node(cls):
    _new_nodes.append(cls)
    return cls


@_new_node
class directive(docutils.nodes.Element):
    pass


@_new_node
class role(docutils.nodes.Element):
    def __init__(self, rawtext, escaped_text, **options):
        super().__init__(rawtext, escaped_text=escaped_text, options=options)


_new_directives = []


def _add_directive(name, cls, option_spec=None, raw=True):
    _new_directives.append((name, cls, option_spec, raw))


def _subclasses(cls):
    for c in cls.__subclasses__():
        yield c
        yield from _subclasses(c)


# Add support for common directives.


# `list-table` directives are parsed into table nodes by default and could be formatted as such, but
# that's vulnerable to producing malformed tables when the given column widths are too small.
_add_directive("list-table", directives.tables.ListTable, raw=False)

_add_directive("contents", directives.parts.Contents)
_add_directive("include", directives.misc.Include)
_add_directive("toctree", sphinx.directives.other.TocTree)


for d in set(_subclasses(autodoc.Documenter)):
    if d.objtype != "object":
        _add_directive(
            "auto" + d.objtype, autodoc.directive.AutodocDirective, option_spec=d.option_spec
        )


try:
    import sphinxarg.ext

    _add_directive("argparse", sphinxarg.ext.ArgParseDirective)
except ImportError:
    pass


def register():
    docutils.nodes._add_node_class_names([cls.__name__ for cls in _new_nodes])

    for r in ["class", "download", "func", "ref", "superscript"]:
        roles.register_canonical_role(r, roles.GenericRole(r, role))

    identity = lambda x: x
    run = lambda self: [directive(directive=self)]

    for name, cls, option_spec, raw in _new_directives:
        if option_spec is None:
            option_spec = cls.option_spec
        namespace = {"option_spec": {k: identity for k in option_spec}, "run": run, "raw": raw}
        directives.register_directive(name, type("rstfmt_" + cls.__name__, (cls,), namespace))
