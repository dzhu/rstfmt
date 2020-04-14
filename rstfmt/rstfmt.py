import itertools
import re
import string
from collections import namedtuple

import docutils
import docutils.parsers.rst

from . import rst_extras

# Constants.


# The non-overlined characters from https://devguide.python.org/documenting/#sections, plus some.
section_chars = '=-^"~+'

# https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#inline-markup-recognition-rules
space_chars = set(string.whitespace)
pre_markup_break_chars = space_chars | set("-:/'\"<([{")
post_markup_break_chars = space_chars | set("-.,:;!?\\/'\")]}>")


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
        if self.width is None:
            return self
        return self._replace(width=max(1, self.width - n))

    def in_section(self):
        return self._replace(section_depth=self.section_depth + 1)

    def with_width(self, w):
        return self._replace(width=w)

    def with_bullet(self, bullet):
        return self._replace(bullet=bullet)

    def with_colwidths(self, c):
        return self._replace(colwidths=c)


class inline_markup:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "inline_markup({})".format(repr(self.text))


word_info = namedtuple(
    "word_info", ["text", "in_markup", "start_space", "end_space", "start_punct", "end_punct"],
)


def split_words(item):
    if isinstance(item, str):
        if not item:
            # An empty string is treated as having trailing punctuation: it only
            # shows up when two inline markup blocks are separated by
            # backslash-space, and this means that after it is merged with its
            # predecessor the resulting word will not cause a second escape to
            # be introduced when merging with the successor.
            new_words = [word_info(item, False, False, False, False, True)]
        else:
            new_words = [word_info(s, False, False, False, False, False) for s in item.split()]
            if item:
                if not new_words:
                    new_words = [word_info("", False, True, True, True, True)]
                if item[0] in space_chars:
                    new_words[0] = new_words[0]._replace(start_space=True)
                if item[-1] in space_chars:
                    new_words[-1] = new_words[-1]._replace(end_space=True)
                if item[0] in post_markup_break_chars:
                    new_words[0] = new_words[0]._replace(start_punct=True)
                if item[-1] in pre_markup_break_chars:
                    new_words[-1] = new_words[-1]._replace(end_punct=True)
    elif isinstance(item, inline_markup):
        new_words = [word_info(s, True, False, False, False, False) for s in item.text.split()]
    return new_words


def wrap_text(width, items):
    items = list(items)
    raw_words = list(chain(map(split_words, items)))

    words = [word_info("", False, True, True, True, True)]
    for word in raw_words:
        last = words[-1]
        if not last.in_markup and word.in_markup and not last.end_space:
            join = "" if last.end_punct else r"\ "
            words[-1] = word_info(last.text + join + word.text, True, False, False, False, False)
        elif last.in_markup and not word.in_markup and not word.start_space:
            join = "" if word.start_punct else r"\ "
            words[-1] = word_info(
                last.text + join + word.text,
                False,
                False,
                word.end_space,
                word.start_punct,
                word.end_punct,
            )
        else:
            words.append(word)

    words = (word.text for word in words if word.text)

    if width is None:
        yield " ".join(words)
        return

    buf = []
    n = 0
    for w in words:
        n2 = n + bool(buf) + len(w)
        if buf and n2 > width:
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
    node.children = [c for c in node.children if not isinstance(c, docutils.nodes.system_message)]
    for c in node.children:
        preproc(c)

    for a, b in pairwise(node.children):
        if isinstance(a, docutils.nodes.reference) and isinstance(b, docutils.nodes.target):
            a.attributes["target"] = b


# Main stuff.


class Formatters:
    # Basic formatting.
    @staticmethod
    def substitution_reference(node, ctx: FormatContext):
        yield inline_markup("|" + "".join(chain(fmt_children(node, ctx))) + "|")

    @staticmethod
    def emphasis(node, ctx: FormatContext):
        yield inline_markup("*" + "".join(chain(fmt_children(node, ctx))) + "*")

    @staticmethod
    def strong(node, ctx: FormatContext):
        yield inline_markup("**" + "".join(chain(fmt_children(node, ctx))) + "**")

    @staticmethod
    def literal(node, ctx: FormatContext):
        yield inline_markup("``" + "".join(chain(fmt_children(node, ctx))) + "``")

    @staticmethod
    def title_reference(node, ctx: FormatContext):
        yield inline_markup("`" + "".join(chain(fmt_children(node, ctx))) + "`")

    # Basic lists.
    @staticmethod
    def _list(node, ctx: FormatContext):
        subs = [list(fmt(c, ctx)) for c in node.children]
        if any(len(s) > 2 for s in subs):
            yield from chain_intersperse("", subs)
        else:
            yield from chain(subs)

    @staticmethod
    def bullet_list(node, ctx: FormatContext):
        yield from Formatters._list(node, ctx.with_bullet("- "))

    @staticmethod
    def enumerated_list(node, ctx: FormatContext):
        yield from Formatters._list(node, ctx.with_bullet("#."))

    @staticmethod
    def list_item(node, ctx: FormatContext):
        w = len(ctx.bullet) + 1
        b = ctx.bullet + " "
        s = " " * w
        ctx = ctx.indent(w)
        for first, c in enum_first(chain_intersperse("", fmt_children(node, ctx))):
            yield ((b if first else s) if c else "") + c

    # Definition lists.
    @staticmethod
    def term(node, ctx: FormatContext):
        yield " ".join(wrap_text(0, chain(fmt_children(node, ctx))))

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

    # Field lists.
    @staticmethod
    def field_name(node, ctx: FormatContext):
        text = " ".join(wrap_text(0, chain(fmt_children(node, ctx))))
        yield f":{text}:"

    @staticmethod
    def field_body(node, ctx: FormatContext):
        yield from with_spaces(3, chain(fmt_children(node, ctx.indent(3))))

    @staticmethod
    def field(node, ctx: FormatContext):
        yield from chain(fmt_children(node, ctx))

    @staticmethod
    def field_list(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Structure.
    @staticmethod
    def transition(node, ctx: FormatContext):
        yield "----"

    @staticmethod
    def paragraph(node, ctx: FormatContext):
        yield from wrap_text(ctx.width, chain(fmt_children(node, ctx)))

    @staticmethod
    def title(node, ctx: FormatContext):
        text = " ".join(wrap_text(0, chain(fmt_children(node, ctx))))
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

        if d.raw:
            yield from prepend_if_any("", with_spaces(3, d.content))
        else:
            sub_doc = parse_string("\n".join(d.content))
            yield ""
            yield from with_spaces(3, fmt(sub_doc, ctx.indent(3)))

    @staticmethod
    def section(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx.in_section()))

    @staticmethod
    def document(node, ctx: FormatContext):
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Tables.
    @staticmethod
    def row(node, ctx: FormatContext):
        all_lines = [
            chain_intersperse("", fmt_children(entry, ctx.with_width(w - 2)))
            for entry, w in zip(node.children, ctx.colwidths)
        ]
        for line_group in itertools.zip_longest(*all_lines):
            yield "|" + "|".join(
                " " + (line or "").ljust(w - 2) + " " for line, w in zip(line_group, ctx.colwidths)
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
        title = " ".join(wrap_text(0, chain(fmt_children(node, ctx))))
        anonymous = (
            ("target" not in node.attributes)
            if "refuri" in node.attributes
            else (node.attributes.get("anonymous"))
        )
        suffix = "__" if anonymous else "_"

        if "refuri" in node.attributes:
            uri = node.attributes["refuri"]
            # Do a basic check for standalone hyperlinks.
            if uri == title or uri == "mailto:" + title:
                yield inline_markup(title)
            else:
                yield inline_markup(f"`{title} <{uri}>`{suffix}")
        else:
            # Reference names can consist of "alphanumerics plus isolated (no two adjacent) internal
            # hyphens, underscores, periods, colons and plus signs", according to
            # https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#reference-names.
            is_single_word = (
                re.match("^[-_.:+a-zA-Z]+$", title) and not re.search("[-_.:+][-_.:+]", title)
            ) or (
                len(node.children) == 1
                and isinstance(node.children[0], docutils.nodes.substitution_reference)
            )
            if not is_single_word:
                title = "`" + title + "`"
            yield inline_markup(title + suffix)

    @staticmethod
    def role(node, ctx: FormatContext):
        yield inline_markup(node.rawsource)

    @staticmethod
    def inline(node, ctx: FormatContext):
        yield from chain(fmt_children(node, ctx))

    @staticmethod
    def target(node, ctx: FormatContext):
        if not isinstance(node.parent, (docutils.nodes.document, docutils.nodes.section)):
            return
        try:
            body = " " + node.attributes["refuri"]
        except KeyError:
            body = ""
        if node.attributes.get("anonymous"):
            head = "__ .."
        else:
            head = f".. _{node.attributes['names'][0]}:"
        yield head + body

    @staticmethod
    def comment(node, ctx: FormatContext):
        yield ".."
        text = "\n".join(chain(fmt_children(node, ctx)))
        yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def note(node, ctx: FormatContext):
        yield ".. note::"
        yield ""
        yield from with_spaces(3, chain_intersperse("", fmt_children(node, ctx.indent(3))))

    @staticmethod
    def warning(node, ctx: FormatContext):
        yield ".. warning::"
        yield ""
        yield from with_spaces(3, chain_intersperse("", fmt_children(node, ctx.indent(3))))

    @staticmethod
    def hint(node, ctx: FormatContext):
        yield ".. hint::"
        yield ""
        yield from with_spaces(3, chain_intersperse("", fmt_children(node, ctx.indent(3))))

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
    try:
        func = getattr(Formatters, type(node).__name__)
    except AttributeError:
        raise ValueError(f"Unknown node type {type(node).__name__}!")
    return func(node, ctx)


def format_node(width, node):
    if width <= 0:
        width = None
    return "\n".join(fmt(node, FormatContext(0, width, None, None))) + "\n"


def parse_string(s):
    parser = docutils.parsers.rst.Parser()
    settings = docutils.frontend.OptionParser(
        components=[docutils.parsers.rst.Parser,]
    ).get_default_values()
    settings.report_level = docutils.utils.Reporter.SEVERE_LEVEL
    settings.halt_level = docutils.utils.Reporter.WARNING_LEVEL
    settings.file_insertion_enabled = False
    doc = docutils.utils.new_document("", settings=settings)
    parser.parse(s, doc)
    preproc(doc)

    return doc
