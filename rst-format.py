#!/usr/bin/env python

import argparse
import contextlib
import functools
import itertools
import sys
from collections import namedtuple

import docutils
import docutils.parsers.rst
import docutils.parsers.rst.directives.parts
import sphinx.directives
import sphinx.ext.autodoc.directive
from docutils.parsers.rst import directives, roles

# Handle directives by inserting them into the tree unparsed.


def register_node(cls):
    docutils.nodes._add_node_class_names([cls.__name__])
    return cls


@register_node
class directive(docutils.nodes.Element):
    pass


class generic_directive(docutils.parsers.rst.Directive):
    def run(self):
        return [directive(directive=self)]


# Add support for common directives.


def identity(x):
    return x


def register_directive(name):
    def proc(cls):
        # Make sure all arguments are passed through without change.
        cls.option_spec = {k: identity for k in cls.option_spec}
        directives.register_directive(name, cls)

    return proc


@register_directive("toctree")
class toctree_directive(generic_directive, sphinx.directives.other.TocTree):
    pass


for d in [
    sphinx.ext.autodoc.ClassDocumenter,
    sphinx.ext.autodoc.ModuleDocumenter,
    sphinx.ext.autodoc.FunctionDocumenter,
    sphinx.ext.autodoc.MethodDocumenter,
]:

    register_directive("auto" + d.objtype)(
        type(
            f"autodoc_{d.objtype}_directive",
            (generic_directive, sphinx.ext.autodoc.directive.AutodocDirective),
            {"option_spec": d.option_spec},
        )
    )


try:
    import sphinxarg.ext

    @register_directive("argparse")
    class argparse_directive(generic_directive, sphinxarg.ext.ArgParseDirective):
        pass


except ImportError:
    pass


@register_directive("contents")
class contents_directive(generic_directive, directives.parts.Contents):
    pass


@register_node
class role(docutils.nodes.Element):
    def __init__(self, rawtext, escaped_text, **options):
        super().__init__(rawtext, escaped_text=escaped_text, options=options)


class DumpVisitor(docutils.nodes.GenericNodeVisitor):
    def __init__(self, document):
        super().__init__(document)
        self.depth = 0

    def default_visit(self, node):
        t = type(node).__name__
        print("    " * self.depth + f"- \x1b[34m{t}\x1b[m", end=" ")
        if isinstance(node, docutils.nodes.Text):
            print(repr(node.astext()[:100]), end="")
        else:
            print({k: v for k, v in node.attributes.items() if v}, end="")
        print()

        self.depth += 1

    def default_departure(self, node):
        self.depth -= 1


# Constants.


section_chars = '=-~^"'


# Iterator stuff.


def intersperse(val, it):
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield x


chain = itertools.chain.from_iterable


def enum_first(it):
    return zip(itertools.chain([True], itertools.repeat(False)), it)


def prepend_if_any(f, it):
    try:
        x = next(it)
    except StopIteration:
        return
    yield f
    yield x
    yield from it


def chain_intersperse(val, it):
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield from x


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


# Helper classes and functions.


class FormatContext(
    namedtuple("FormatContextBase", ["section_depth", "width", "bullet", "colwidths"])
):
    def indent(self, n):
        return self._replace(width=self.width - n)

    def in_section(self):
        return self._replace(section_depth=self.section_depth + 1)

    def with_width(self, w):
        return self._replace(width=w)

    def with_bullet(self, bullet):
        return self._replace(bullet=bullet)

    def with_colwidths(self, c):
        return self._replace(colwidths=c)


# Define this here to support Python <3.7.
class nullcontext(contextlib.AbstractContextManager):
    def __init__(self, enter_result=None):
        self.enter_result = enter_result

    def __enter__(self):
        return self.enter_result

    def __exit__(self, *excinfo):
        pass


def wrap_text(width, text):
    buf = []
    n = 0
    for w in text.split():
        n2 = n + bool(buf) + len(w)
        if n2 > width:
            yield " ".join(buf)
            buf = []
            n2 = len(w)
        buf.append(w)
        n = n2
    if buf:
        yield " ".join(buf)


def fmt_children(node, ctx):
    return (fmt(c, ctx) for c in node.children)


def with_spaces(n, lines):
    s = " " * n
    for l in lines:
        yield s + l if l else l


def preproc(node):
    """
    Do some node preprocessing that is generic across node types and is therefore most convenient to
    do as a simple recursive function rather than as part of the big dispatcher class.
    """
    node.children = [
        c for c in node.children if not isinstance(c, docutils.nodes.system_message)
    ]
    for c in node.children:
        preproc(c)

    for a, b in pairwise(node.children):
        if isinstance(a, docutils.nodes.reference) and isinstance(
            b, docutils.nodes.target
        ):
            a.attributes["target"] = b


# Main stuff.


class Formatters:
    # Basic formatting.
    @staticmethod
    def substitution_reference(node, ctx: FormatContext):
        yield "\\ |" + "".join(chain(fmt_children(node, ctx))) + "|\\ "

    @staticmethod
    def emphasis(node, ctx: FormatContext):
        yield "*" + "".join(chain(fmt_children(node, ctx))) + "*"

    @staticmethod
    def strong(node, ctx: FormatContext):
        yield "**" + "".join(chain(fmt_children(node, ctx))) + "**"

    @staticmethod
    def literal(node, ctx: FormatContext):
        yield "``" + "".join(chain(fmt_children(node, ctx))) + "``"

    @staticmethod
    def title_reference(node, ctx: FormatContext):
        yield "`" + "".join(chain(fmt_children(node, ctx))) + "`"

    # Lists.
    @staticmethod
    def bullet_list(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx.with_bullet("- ")))

    @staticmethod
    def enumerated_list(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx.with_bullet("#.")))

    @staticmethod
    def list_item(node, ctx: FormatContext):
        w = len(ctx.bullet) + 1
        b = ctx.bullet + " "
        s = " " * w
        ctx = ctx.indent(w)
        for first, c in enum_first(chain_intersperse("", fmt_children(node, ctx))):
            yield ((b if first else s) if c else "") + c

    @staticmethod
    def term(node, ctx: FormatContext):
        yield "".join(chain(fmt_children(node, ctx)))

    @staticmethod
    def definition(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    @staticmethod
    def definition_list_item(node, ctx: FormatContext):
        for c in node.children:
            if isinstance(c, docutils.nodes.term):
                yield from fmt(c, ctx)
            elif isinstance(c, docutils.nodes.definition):
                yield from with_spaces(3, fmt(c, ctx.indent(3)))

    @staticmethod
    def definition_list(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Structure.
    @staticmethod
    def paragraph(node, ctx: FormatContext):
        yield from wrap_text(ctx.width, "".join(chain(fmt_children(node, ctx))))

    @staticmethod
    def title(node, ctx: FormatContext):
        text = "".join(chain(fmt(c, ctx) for c in node.children))
        yield text
        yield section_chars[ctx.section_depth - 1] * len(text)

    @staticmethod
    def block_quote(node, ctx: FormatContext):
        yield from with_spaces(
            3, chain_intersperse("", fmt_children(node, ctx.indent(3))),
        )

    @staticmethod
    def directive(node, ctx: FormatContext):
        d = node.attributes["directive"]

        yield " ".join([f".. {d.name}::", *d.arguments])
        # Just rely on the order being stable, hopefully.
        for k, v in d.options.items():
            yield f"   :{k}:" if v is None else f"   :{k}: {v}"
        yield from prepend_if_any("", with_spaces(3, d.content))

    @staticmethod
    def section(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx.in_section()))

    @staticmethod
    def document(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Tables.
    @staticmethod
    def row(node, ctx: FormatContext):
        # sep = "|" + "|".join(" " * w for w in ctx.colwidths) + "|"
        # yield sep

        all_lines = [
            chain_intersperse("", fmt_children(entry, ctx.with_width(w - 2)))
            for entry, w in zip(node.children, ctx.colwidths)
        ]
        for line_group in itertools.zip_longest(*all_lines):
            yield "|" + "|".join(
                " " + (line or "").ljust(w - 2) + " "
                for line, w in zip(line_group, ctx.colwidths)
            ) + "|"

    @staticmethod
    def tbody(node, ctx: FormatContext):
        sep = "+" + "+".join("-" * w for w in ctx.colwidths) + "+"
        yield from chain_intersperse(sep, fmt_children(node, ctx))

    thead = tbody

    @staticmethod
    def tgroup(node, ctx: FormatContext):
        ctx = ctx.with_colwidths(
            [
                c.attributes["colwidth"]
                for c in node.children
                if isinstance(c, docutils.nodes.colspec)
            ]
        )
        sep = "+" + "+".join("-" * w for w in ctx.colwidths) + "+"

        yield sep
        for c in node.children:
            if isinstance(c, docutils.nodes.colspec):
                continue
            if isinstance(c, docutils.nodes.thead):
                yield from fmt(c, ctx)
                yield "+" + "+".join("=" * w for w in ctx.colwidths) + "+"
            if isinstance(c, docutils.nodes.tbody):
                yield from fmt(c, ctx)
                yield sep

    @staticmethod
    def table(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Misc.
    @staticmethod
    def Text(node, _: FormatContext):
        yield node.astext()

    @staticmethod
    def reference(node, ctx: FormatContext):
        title = node.children[0].astext()
        uri = node.attributes["refuri"]
        suffix = "_" if "target" in node.attributes else "__"
        yield f"`{title} <{uri}>`{suffix}"

    @staticmethod
    def role(node, ctx: FormatContext):
        yield node.rawsource

    @staticmethod
    def inline(node, ctx: FormatContext):
        yield from chain(fmt_children(node, ctx))

    @staticmethod
    def target(node, ctx: FormatContext):
        if isinstance(node.parent, (docutils.nodes.document, docutils.nodes.section)):
            yield f".. _{node.attributes['names'][0]}:"

    @staticmethod
    def comment(node, ctx: FormatContext):
        yield ".."
        text = "\n".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def note(node, ctx: FormatContext):
        yield ".. note::"
        yield ""
        yield from with_spaces(
            3, chain_intersperse("", fmt_children(node, ctx.indent(3)))
        )

    @staticmethod
    def warning(node, ctx: FormatContext):
        yield ".. warning::"
        yield ""
        yield from with_spaces(
            3, chain_intersperse("", fmt_children(node, ctx.indent(3)))
        )

    @staticmethod
    def hint(node, ctx: FormatContext):
        yield ".. hint::"
        yield ""
        yield from with_spaces(
            3, chain_intersperse("", fmt_children(node, ctx.indent(3)))
        )

    @staticmethod
    def image(node, ctx: FormatContext):
        yield f".. image:: {node.attributes['uri']}"

    @staticmethod
    def literal_block(node, ctx: FormatContext):
        lang = [c for c in node.attributes["classes"] if c != "code"]
        yield ".. code::" + (" " + lang[0] if lang else "")
        yield ""
        text = "".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))


def fmt(node, ctx: FormatContext):
    func = getattr(
        Formatters,
        type(node).__name__,
        lambda _, __: ["\x1b[35m{}\x1b[m".format(type(node).__name__.upper())],
    )
    # print(type(node).__name__, list(func(node, ctx)))
    return func(node, ctx)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-place", action="store_true")
    parser.add_argument("-w", "--width", type=int, default=72)
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(args)

    if not args.files:
        args.files = ["-"]

    for r in ["class", "download", "func", "ref", "superscript"]:
        roles.register_canonical_role(r, roles.GenericRole(r, role))

    parser = docutils.parsers.rst.Parser()

    for fn in args.files:
        doc = docutils.utils.new_document(
            "",
            settings=docutils.frontend.OptionParser(
                components=(docutils.parsers.rst.Parser,)
            ).get_default_values(),
        )

        cm = nullcontext(sys.stdin) if fn == "-" else open(fn)
        with cm as f:
            parser.parse(f.read(), doc)

        preproc(doc)

        if not args.quiet:
            print("=" * 60, fn)
            doc.walkabout(DumpVisitor(doc))
            # doc.walkabout(FormatVisitor(doc))

        cm = open(fn, "w") if args.in_place else nullcontext(sys.stdout)
        with cm as f:
            print("\n".join(fmt(doc, FormatContext(0, args.width, None, None))), file=f)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
