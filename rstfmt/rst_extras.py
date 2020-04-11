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


# Add support for common directives.


# `list-table` directives are parsed as table nodes and could be formatted as such, but that's
# vulnerable to producing malformed tables when the given column widths are too small. TODO: The
# contents of some directives, including `list-table`, should be parsed and formatted as normal
# reST, but we currently dump all directive bodies unchanged.
_new_directives = [
    ("list-table", directives.tables.ListTable, None),
    ("contents", directives.parts.Contents, None),
    ("toctree", sphinx.directives.other.TocTree, None),
]


def _subclasses(cls):
    for c in cls.__subclasses__():
        yield c
        yield from _subclasses(c)


for d in set(_subclasses(autodoc.Documenter)):
    if d.objtype == "object":
        continue
    _new_directives.append(("auto" + d.objtype, autodoc.directive.AutodocDirective, d.option_spec))

try:
    import sphinxarg.ext

    _new_directives.append(("argparse", sphinxarg.ext.ArgParseDirective, None))
except ImportError:
    pass


def register():
    docutils.nodes._add_node_class_names([cls.__name__ for cls in _new_nodes])

    for r in ["class", "download", "func", "ref", "superscript"]:
        roles.register_canonical_role(r, roles.GenericRole(r, role))

    identity = lambda x: x
    directive_run = lambda self: [directive(directive=self)]

    for name, cls, option_spec in _new_directives:
        if option_spec is None:
            option_spec = cls.option_spec
        namespace = {"option_spec": {k: identity for k in option_spec}, "run": directive_run}
        directives.register_directive(name, type("rstfmt_" + cls.__name__, (cls,), namespace))
