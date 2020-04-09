#!/usr/bin/env python

import itertools
import sys
from collections import namedtuple

import docutils
import docutils.parsers.rst
from docutils.parsers.rst import directives, roles

import sphinx.directives


class RefNode(docutils.nodes.Element):
    pass


class directive(docutils.nodes.Element):
    def __init__(self, d):
        super().__init__("", directive=d)


class generic_directive(docutils.parsers.rst.Directive):
    has_content = True

    def run(self):
        return [directive(self)]


class toctree_directive(generic_directive):
    option_spec = sphinx.directives.other.TocTree.option_spec


directives.register_directive("toctree", toctree_directive)


try:
    import sphinxarg.ext

    class argparse_directive(generic_directive):
        option_spec = sphinxarg.ext.ArgParseDirective.option_spec

    directives.register_directive("argparse", argparse_directive)
except ImportError:
    pass


class XRefRole(sphinx.roles.XRefRole):
    def run(self):
        # TODO Actually need to handle the case where the title and target are
        # both specified but equal.
        return (
            [
                docutils.nodes.reference(
                    "",
                    docutils.nodes.Text(self.title),
                    docutils.nodes.Text(self.target),
                )
            ],
            [],
        )


docutils.nodes._add_node_class_names(["directive"])


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


FormatContext = namedtuple("FormatContext", ["section_depth", "width"])
section_chars = '=-~^"'


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


WIDTH = 72


def intersperse(val, it):
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield x


chain = itertools.chain.from_iterable


def chain_intersperse(val, it):
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield from x


def with_spaces(n, lines):
    s = " " * n
    for l in lines:
        yield s + l if l else l


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

    # Lists.
    @staticmethod
    def bullet_list(node, ctx: FormatContext):
        for c in node.children:
            assert isinstance(c, docutils.nodes.list_item)
            f = fmt(c, ctx._replace(width=ctx.width - 2))
            yield "- " + next(f)
            yield from with_spaces(2, f)

    @staticmethod
    def enumerated_list(node, ctx: FormatContext):
        for c in node.children:
            assert isinstance(c, docutils.nodes.list_item)
            f = fmt(c, ctx._replace(width=ctx.width - 2))
            yield "#. " + next(f)
            yield from with_spaces(3, f)

    @staticmethod
    def list_item(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

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
                yield from with_spaces(3, fmt(c, ctx))

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
            3,
            chain_intersperse(
                "", fmt_children(node, ctx._replace(width=ctx.width - 2))
            ),
        )

    @staticmethod
    def directive(node, ctx: FormatContext):
        d = node.attributes["directive"]
        # TODO: args?
        yield f".. {d.name}::"
        # Just rely on the order being stable, hopefully.
        for k, v in d.options.items():
            yield f"   :{k}:" if v is None else f"   :{k}: {v}"
        yield ""
        yield from with_spaces(3, d.content)

    @staticmethod
    def section(node, ctx: FormatContext):
        yield from chain_intersperse(
            "", fmt_children(node, ctx._replace(section_depth=ctx.section_depth + 1))
        )

    @staticmethod
    def document(node, ctx):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Misc.
    @staticmethod
    def Text(node, _: FormatContext):
        yield node.astext()

    @staticmethod
    def reference(node, ctx: FormatContext):
        if "refuri" in node.attributes:
            title = node.children[0].astext()
            uri = node.attributes["refuri"]
            yield f"`{title} <{uri}>`_"
            return
        title, target = (c.astext() for c in node.children)
        if title == target:
            yield f":ref:`{target}`"
        else:
            yield f":ref:`{title} <{target}>`"

    @staticmethod
    def target(node, ctx: FormatContext):
        yield from []

    @staticmethod
    def comment(node, ctx: FormatContext):
        yield ".."
        text = "\n".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def note(node, ctx: FormatContext):
        yield ".. note::"
        yield ""
        text = "\n".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def warning(node, ctx: FormatContext):
        yield ".. warning::"
        yield ""
        text = "\n".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def literal_block(node, ctx: FormatContext):
        # TODO put the right language here
        yield ".. code::"
        yield ""
        text = "\n".join(chain(fmt_children(node, ctx)))
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
    roles.register_local_role("class", XRefRole())
    roles.register_local_role("download", XRefRole())
    roles.register_local_role("ref", XRefRole())

    parser = docutils.parsers.rst.Parser()

    quiet = False
    for fn in args:
        if fn == "-q":
            quiet = True
            continue
        doc = docutils.utils.new_document(
            "",
            settings=docutils.frontend.OptionParser(
                components=(docutils.parsers.rst.Parser,)
            ).get_default_values(),
        )
        parser.parse(open(fn).read(), doc)

        if not quiet:
            print("=" * 60, fn)
            doc.walkabout(DumpVisitor(doc))
            # doc.walkabout(FormatVisitor(doc))

        print("\n".join(fmt(doc, FormatContext(0, WIDTH))))


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
