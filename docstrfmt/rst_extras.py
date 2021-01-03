"""This module handles adding constructs to the reST parser in a way that makes sense for
docstrfmt. Nonstandard directives and roles are inserted into the tree unparsed (wrapped
in custom node classes defined here) so we can format them the way they came in without
without caring about what they would normally expand to.

"""

from typing import Any, Iterator, List, Tuple, Type, TypeVar

import docutils
import sphinx.directives
import sphinx.ext.autodoc.directive
from docutils.parsers.rst import directives, roles
from docutils.parsers.rst.directives import parts

# Import these only to load their domain subclasses.
from sphinx.domains import c, cpp, python  # noqa: F401
from sphinx.ext import autodoc, autosummary

T = TypeVar("T")


class directive(docutils.nodes.Element):
    pass


class role(docutils.nodes.Element):
    pass


class ref_role(docutils.nodes.Element):
    pass


class ReferenceRole(sphinx.util.docutils.ReferenceRole):
    def run(
        self,
    ) -> Tuple[List[docutils.nodes.Node], List[docutils.nodes.system_message]]:
        node = ref_role(
            self.rawtext,
            name=self.name,
            has_explicit_title=self.has_explicit_title,
            target=self.target,
            title=self.title,
        )
        return [node], []


role_aliases = {
    "pep": "PEP",
    "pep-reference": "PEP",
    "rfc": "RFC",
    "rfc-reference": "RFC",
    "subscript": "sub",
    "superscript": "sup",
}


def generic_role(r: str, rawtext: str, text: str, *_: Any, **__: Any) -> Any:
    r = role_aliases.get(r.lower(), r)
    text = docutils.utils.unescape(text, restore_backslashes=True)
    return [role(rawtext, text=text, role=r)], []


def _add_directive(
    name: str,
    cls: Type[docutils.parsers.rst.Directive],
    *,
    raw: bool = True,
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
    directives.register_directive(
        name, type(f"docstrfmt_{cls.__name__}", (cls,), namespace)
    )


def _subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    for subclass in cls.__subclasses__():
        yield subclass
        yield from _subclasses(subclass)


def register() -> None:
    for r in [
        # Standard roles (https://docutils.sourceforge.io/docs/ref/rst/roles.html) that don't have
        # equivalent non-role-based markup.
        "math",
        "pep-reference",
        "rfc-reference",
        "subscript",
        "superscript",
    ]:
        roles.register_canonical_role(r, generic_role)

    roles.register_canonical_role("download", ReferenceRole())
    for domain in _subclasses(sphinx.domains.Domain):
        for name, role_callable in domain.roles.items():
            if isinstance(role_callable, sphinx.util.docutils.ReferenceRole):
                roles.register_canonical_role(name, ReferenceRole())
                roles.register_canonical_role(f"{domain.name}:{name}", ReferenceRole())

    # `list-table` directives are parsed into table nodes by default and could be formatted as such,
    # but that's vulnerable to producing malformed tables when the given column widths are too
    # small.

    _add_directive("autosummary", autosummary.Autosummary)
    _add_directive("contents", parts.Contents)
    _add_directive("deprecated", sphinx.directives.other.VersionChange, raw=False)
    _add_directive("figure", directives.images.Figure, raw=False)
    _add_directive("image", directives.images.Image)
    _add_directive("include", directives.misc.Include)
    _add_directive("list-table", directives.tables.ListTable, raw=False)
    _add_directive("literalinclude", sphinx.directives.code.LiteralInclude)
    _add_directive("math", directives.body.MathBlock)
    _add_directive("raw", directives.misc.Raw)
    _add_directive("rst-class", sphinx.directives.other.Class)
    _add_directive("seealso", sphinx.directives.other.SeeAlso, raw=False)
    _add_directive("toctree", sphinx.directives.other.TocTree)
    _add_directive("versionadded", sphinx.directives.other.VersionChange, raw=False)
    _add_directive("versionchanged", sphinx.directives.other.VersionChange, raw=False)

    for d in set(_subclasses(autodoc.Documenter)):
        if d.objtype != "object":
            _add_directive(
                f"auto{d.objtype}", autodoc.directive.AutodocDirective, raw=False
            )

    try:
        import sphinxarg.ext
    except ImportError:
        pass
    else:  # pragma: no cover
        _add_directive("argparse", sphinxarg.ext.ArgParseDirective)
