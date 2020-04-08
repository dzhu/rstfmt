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


class TocTree(sphinx.directives.TocTree):
    def run(self):
        return []


class XRefRole(sphinx.roles.XRefRole):
    def run(self):
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


class FormatVisitor(docutils.nodes.GenericNodeVisitor):
    section_chars = '=-~^"'

    def __init__(self, document):
        super().__init__(document)
        self.section_depth = -1
        self.buf = []

    def visit_Text(self, node):
        self.buf.append(node.astext())

    def visit_substitution_reference(self, _):
        self.buf.append("\\ |")

    def depart_substitution_reference(self, _):
        self.buf.append("|\\ ")

    def visit_section(self, _):
        self.section_depth += 1

    def depart_section(self, _):
        self.section_depth -= 1

    def visit_title(self, _):
        if self.buf:
            print("WARNING: non-empty buf on visiting title", self.buf, file=sys.stderr)
        self.buf = []

    def depart_title(self, _):
        text = "".join(self.buf)
        self.buf = []
        print(text)
        print(self.section_chars[self.section_depth] * len(text))
        print()

    def visit_strong(self, _):
        self.buf.append("*")

    def depart_strong(self, _):
        self.buf.append("*")

    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass


# def show_node(node, depth=0):
#     print("    " * depth + "- " + type(node).__name__, end="")
#     if isinstance(node, docutils.nodes.Text):
#         print(" " + repr(node.astext()[:100]), end="")
#     print()
#     for c in node.children:
#         show_node(c, depth + 1)


FormatContext = namedtuple("FormatContext", ["section_depth", "indent_depth"])
section_chars = '=-~^"'


def wrap_text(width, text):
    # TODO
    return text


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


def with_spaces(n, lines):
    s = " " * n
    for l in lines:
        yield s + l


class Formatters:
    @staticmethod
    def emphasis(node, ctx: FormatContext):
        return "*" + "".join(fmt_children(node, ctx)) + "*"

    @staticmethod
    def strong(node, ctx: FormatContext):
        return "**" + "".join(fmt_children(node, ctx)) + "**"

    @staticmethod
    def substitution_reference(node, ctx: FormatContext):
        return "\\ |" + "".join(fmt_children(node, ctx)) + "|\\ "

    @staticmethod
    def Text(node, _: FormatContext):
        return node.astext()

    @staticmethod
    def paragraph(node, ctx: FormatContext):
        return wrap_text(WIDTH - 3 * ctx.indent_depth, "".join(fmt_children(node, ctx)))

    @staticmethod
    def bullet_list(node, ctx: FormatContext):
        return "\n".join("- " + fmt(c, ctx) for c in node.children)

    @staticmethod
    def list_item(node, ctx: FormatContext):
        return "\n\n".join(fmt_children(node, ctx))

    @staticmethod
    def reference(node, ctx: FormatContext):
        if "refuri" in node.attributes:
            title = node.children[0].astext()
            uri = node.attributes["refuri"]
            return f"`{title} <{uri}>`_"
        print(node.children)
        print(node.attributes)
        title, target = (c.astext() for c in node.children)
        if title == target:
            return f":ref:`{target}`"
        return f":ref:`{title} <{target}>`"

    @staticmethod
    def target(node, ctx: FormatContext):
        return ""

    @staticmethod
    def title(node, ctx: FormatContext):
        text = "".join(fmt_children(node, ctx))
        return text + "\n" + section_chars[ctx.section_depth - 1] * len(text)

    @staticmethod
    def section(node, ctx: FormatContext):
        return "\n\n".join(
            fmt_children(node, ctx._replace(section_depth=ctx.section_depth + 1))
        )

    @staticmethod
    def document(node, ctx):
        return "\n\n".join(fmt_children(node, ctx))


def fmt(node, ctx: FormatContext):
    func = getattr(Formatters, type(node).__name__, lambda *args: "")
    return func(node, ctx)


def main(args):
    directives.register_directive("toctree", TocTree)

    roles.register_local_role("class", XRefRole())
    roles.register_local_role("download", XRefRole())
    roles.register_local_role("ref", XRefRole())

    parser = docutils.parsers.rst.Parser()

    for fn in args:
        doc = docutils.utils.new_document(
            "",
            settings=docutils.frontend.OptionParser(
                components=(docutils.parsers.rst.Parser,)
            ).get_default_values(),
        )
        parser.parse(open(fn).read(), doc)

        print("=" * 60, fn)
        doc.walkabout(DumpVisitor(doc))
        # doc.walkabout(FormatVisitor(doc))

        print(fmt(doc, FormatContext(0, 0)))


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
