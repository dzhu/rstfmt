"""
This module handles adding constructs to the reST parser in a way that makes sense for rstfmt.
Nonstandard directives and roles are inserted into the tree unparsed (wrapped in custom node classes
defined here) so we can format them the way they came in without without caring about what they
would normally expand to.
"""

import importlib
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, TypeVar

import docutils
import sphinx.directives
import sphinx.ext.autodoc.directive
from docutils.parsers.rst import Directive, directives, roles

# Import these only to load their domain subclasses.
from sphinx.domains import c, cpp, python  # noqa: F401
from sphinx.ext import autodoc

T = TypeVar("T")


class directive(docutils.nodes.Element, docutils.nodes.Inline):
    pass


class role(docutils.nodes.Element):
    pass


class ref_role(docutils.nodes.Element):
    pass


class ReferenceRole(sphinx.util.docutils.ReferenceRole):
    def run(self) -> Tuple[List[docutils.nodes.Node], List[docutils.nodes.system_message]]:
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
    return ([role(rawtext, text=text, role=r)], [])


def _add_directive(
    name: str,
    cls: Type[docutils.parsers.rst.Directive],
    *,
    attrs: Optional[Dict] = None,
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
        **(attrs or {}),
    }
    directives.register_directive(name, type("rstfmt_" + cls.__name__, (cls,), namespace))


def _subclasses(cls: Type[T]) -> Iterator[Type[T]]:
    for c in cls.__subclasses__():
        yield c
        yield from _subclasses(c)


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
                roles.register_canonical_role(domain.name + ":" + name, ReferenceRole())

    non_raw_directives = {
        "admonition",
        "attention",
        "caution",
        "danger",
        "error",
        "hint",
        "important",
        "note",
        "tip",
        "warning",
        # `list-table` directives are parsed into table nodes by default and could be formatted as
        # such, but that's vulnerable to producing malformed tables when the given column widths are
        # too small, so keep them as directives.
        "list-table",
    }

    # The role directive is defined in a rather odd way under the hood: although it appears to take
    # one argument and allow options, the class actually specifies that it takes no arguments or
    # options but does have content; it then does its own parsing of arguments and options based on
    # the content. I'm not entirely sure why, but I think it's to handle the case of using some
    # exotic base role that has a body or something. I think just taking an argument is pretty much
    # good enough, though.
    _add_directive("role", Directive, attrs={"required_arguments": 1})
    exclude_directives = {"role"}

    for directive_name, (module, cls_name) in directives._directive_registry.items():
        if directive_name in exclude_directives:
            continue
        module = importlib.import_module(f"docutils.parsers.rst.directives.{module}")
        cls = getattr(module, cls_name)
        _add_directive(directive_name, cls, raw=directive_name not in non_raw_directives)

    _add_directive("literalinclude", sphinx.directives.code.LiteralInclude)
    _add_directive("toctree", sphinx.directives.other.TocTree)

    for d in set(_subclasses(autodoc.Documenter)):
        if d.objtype != "object":
            _add_directive("auto" + d.objtype, autodoc.directive.AutodocDirective, raw=False)

    try:
        import sphinxarg.ext
    except ImportError:
        pass
    else:
        _add_directive("argparse", sphinxarg.ext.ArgParseDirective)
