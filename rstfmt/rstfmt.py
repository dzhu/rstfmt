import itertools
import re
import string
import subprocess
import warnings
from collections import namedtuple
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import black
import docutils
import docutils.parsers.rst

T = TypeVar("T")


# Constants.


# The characters from https://devguide.python.org/documenting/#sections.
section_chars = '#*=-^"'
max_overline_depth = 2

# https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#inline-markup-recognition-rules
space_chars = set(string.whitespace)
pre_markup_break_chars = space_chars | set("-:/'\"<([{")
post_markup_break_chars = space_chars | set("-.,:;!?\\/'\")]}>")


# Iterator stuff.


def intersperse(val: T, it: Iterable[T]) -> Iterator[T]:
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield x


chain = itertools.chain.from_iterable


def enum_first(it: Iterable[T]) -> Iterator[Tuple[bool, T]]:
    return zip(itertools.chain([True], itertools.repeat(False)), it)


def prepend_if_any(f: T, it: Iterator[T]) -> Iterator[T]:
    try:
        x = next(it)
    except StopIteration:
        return
    yield f
    yield x
    yield from it


def chain_intersperse(val: T, it: Iterable[Iterable[T]]) -> Iterator[T]:
    first = True
    for x in it:
        if not first:
            yield val
        first = False
        yield from x


def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


# Helper classes and functions.


class FormatContext(NamedTuple):
    section_depth: int
    width: Optional[int]
    bullet: str
    colwidths: List[int]
    line_block_depth: int

    def indent(self, n: int) -> "FormatContext":
        if self.width is None:
            return self
        return self._replace(width=max(1, self.width - n))

    def in_section(self) -> "FormatContext":
        return self._replace(section_depth=self.section_depth + 1)

    def in_line_block(self) -> "FormatContext":
        return self._replace(line_block_depth=self.line_block_depth + 1)

    def with_width(self, w: int) -> "FormatContext":
        return self._replace(width=w)

    def with_bullet(self, bullet: str) -> "FormatContext":
        return self._replace(bullet=bullet)

    def with_colwidths(self, c: List[int]) -> "FormatContext":
        return self._replace(colwidths=c)


class inline_markup:
    def __init__(self, text: str) -> None:
        self.text = text

    def __repr__(self) -> str:
        return "inline_markup({})".format(repr(self.text))


inline_item = Union[str, inline_markup]
inline_iterator = Iterator[inline_item]
line_iterator = Iterator[str]


word_info = namedtuple(
    "word_info", ["text", "in_markup", "start_space", "end_space", "start_punct", "end_punct"],
)


def split_words(item: inline_item) -> List[word_info]:
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


def wrap_text(width: Optional[int], items: Iterable[inline_item]) -> Iterator[str]:
    if width is not None and width <= 0:
        raise ValueError(f"Invalid width {width}")

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

    word_strs = (word.text for word in words if word.text)

    if width is None:
        yield " ".join(word_strs)
        return

    buf: List[str] = []
    n = 0
    for w in word_strs:
        n2 = n + bool(buf) + len(w)
        if buf and n2 > width:
            yield " ".join(buf)
            buf = []
            n2 = len(w)
        buf.append(w)
        n = n2
    if buf:
        yield " ".join(buf)


def fmt_children(node: docutils.nodes.Node, ctx: FormatContext) -> Iterator[Iterator[str]]:
    return (fmt(c, ctx) for c in node.children)


def with_spaces(n: int, lines: Iterable[str]) -> Iterator[str]:
    s = " " * n
    for l in lines:
        yield s + l if l else l


def preproc(node: docutils.nodes.Node) -> None:
    """
    Do some node preprocessing that is generic across node types and is therefore most convenient to
    do as a simple recursive function rather than as part of the big dispatcher class.
    """
    # Strip all system_message nodes. (Just formatting them with no markup isn't enough, since that
    # could lead to extra spaces or empty lines between other elements.)
    node.children = [c for c in node.children if not isinstance(c, docutils.nodes.system_message)]

    # Match references to targets, which helps later with distinguishing whether they're anonymous.
    for a, b in pairwise(node.children):
        if isinstance(a, docutils.nodes.reference) and isinstance(b, docutils.nodes.target):
            a.attributes["target"] = b  # type: ignore

    # Sort contiguous blocks of targets by name.
    start = None
    for i, c in enumerate(itertools.chain(node.children, [None])):
        in_run = start is not None
        is_target = isinstance(c, docutils.nodes.target)
        if in_run and not is_target:
            # Anonymous targets have a value of `[]` for "names", which will sort to the top. Also,
            # it's important here that `sorted` is stable, or anonymous targets could break.
            node.children[start:i] = sorted(
                node.children[start:i], key=lambda t: t.attributes["names"]
            )
            start = None
        elif not in_run and is_target:
            start = i

    # Recurse.
    for c in node.children:
        preproc(c)


class IgnoreMessagesReporter(docutils.utils.Reporter):
    """
    A Docutils error reporter that ignores some messages.

    We want to handle most system messages normally, but it's useful to ignore some (and just doing
    it by level would be too coarse). In particular, having too short a title line leads to a
    warning but parses just fine; ignoring that message means we can automatically fix lengths
    whether they're too short or too long (though they do have to be at least four characters to be
    parsed correctly in the first place).
    """

    ignored_messages = {
        "Title overline too short.",
        "Title underline too short.",
    }

    def system_message(
        self, level: int, message: str, *children: Any, **kwargs: Any
    ) -> docutils.nodes.system_message:
        orig_level = self.halt_level  # type: ignore
        if message in self.ignored_messages:
            self.halt_level = docutils.utils.Reporter.SEVERE_LEVEL + 1
        msg = super().system_message(level, message, *children, **kwargs)
        self.halt_level = orig_level
        return msg


# Main stuff.


class CodeFormatters:
    @staticmethod
    def python(code: str) -> str:
        try:
            code = black.format_str(code, mode=black.FileMode()).rstrip()
        except Exception as e:
            warnings.warn(str(e))
        return code

    @staticmethod
    def go(code: str) -> str:
        try:
            code = subprocess.run(
                ["gofmt"], input=code, stdout=subprocess.PIPE, encoding="utf-8", check=True
            ).stdout
        except OSError as e:
            warnings.warn(str(e))
        except subprocess.CalledProcessError as e:
            warnings.warn(f"gofmt failed: {e.stderr}")
        # gofmt uses tabs; including them in the source will cause docutils to expand them out to
        # tab stops, causing odd spacing in the rendering. Instead, we explicitly convert them into
        # four spaces each, which matches common practice on the Go website. (There are also
        # instances of eight, but not as many, and anyway that looks too wide.)
        return re.sub("^\t+", lambda m: "    " * len(m.group(0)), code, flags=re.MULTILINE)


class Formatters:
    # Basic formatting.
    @staticmethod
    def substitution_reference(
        node: docutils.nodes.substitution_reference, ctx: FormatContext
    ) -> inline_iterator:
        c = chain(fmt_children(node, ctx))
        x = inline_markup("|" + "".join(c) + "|")
        yield x

    @staticmethod
    def emphasis(node: docutils.nodes.emphasis, ctx: FormatContext) -> inline_iterator:
        yield inline_markup("*" + "".join(chain(fmt_children(node, ctx))).replace("*", "\\*") + "*")

    @staticmethod
    def strong(node: docutils.nodes.strong, ctx: FormatContext) -> inline_iterator:
        yield inline_markup(
            "**" + "".join(chain(fmt_children(node, ctx))).replace("*", "\\*") + "**"
        )

    @staticmethod
    def literal(node: docutils.nodes.literal, ctx: FormatContext) -> inline_iterator:
        yield inline_markup("``" + "".join(chain(fmt_children(node, ctx))) + "``")

    @staticmethod
    def title_reference(
        node: docutils.nodes.title_reference, ctx: FormatContext
    ) -> inline_iterator:
        yield inline_markup("`" + "".join(chain(fmt_children(node, ctx))) + "`")

    # Basic lists.
    @staticmethod
    def _list(node: docutils.nodes.Node, ctx: FormatContext) -> line_iterator:
        subs = [list(fmt(c, ctx)) for c in node.children]
        if any(len(s) > 2 for s in subs):
            yield from chain_intersperse("", subs)
        else:
            yield from chain(subs)

    @staticmethod
    def bullet_list(node: docutils.nodes.bullet_list, ctx: FormatContext) -> line_iterator:
        yield from Formatters._list(node, ctx.with_bullet("- "))

    @staticmethod
    def enumerated_list(node: docutils.nodes.enumerated_list, ctx: FormatContext) -> line_iterator:
        yield from Formatters._list(node, ctx.with_bullet("#."))

    @staticmethod
    def list_item(node: docutils.nodes.list_item, ctx: FormatContext) -> line_iterator:
        if not node.children:
            yield "-"
            return
        w = len(ctx.bullet) + 1
        b = ctx.bullet + " "
        s = " " * w
        ctx = ctx.indent(w)
        for first, c in enum_first(chain_intersperse("", fmt_children(node, ctx))):
            yield ((b if first else s) if c else "") + c

    # Definition lists.
    @staticmethod
    def term(node: docutils.nodes.term, ctx: FormatContext) -> line_iterator:
        yield " ".join(wrap_text(None, chain(fmt_children(node, ctx))))

    @staticmethod
    def definition(node: docutils.nodes.definition, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx))

    @staticmethod
    def definition_list_item(
        node: docutils.nodes.definition_list_item, ctx: FormatContext
    ) -> line_iterator:
        for c in node.children:
            if isinstance(c, docutils.nodes.term):
                yield from fmt(c, ctx)
            elif isinstance(c, docutils.nodes.definition):
                yield from with_spaces(3, fmt(c, ctx.indent(3)))

    @staticmethod
    def definition_list(node: docutils.nodes.definition_list, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Field lists.
    @staticmethod
    def field_name(node: docutils.nodes.field_name, ctx: FormatContext) -> line_iterator:
        text = " ".join(wrap_text(None, chain(fmt_children(node, ctx))))
        yield f":{text}:"

    @staticmethod
    def field_body(node: docutils.nodes.field_body, ctx: FormatContext) -> line_iterator:
        yield from with_spaces(3, chain(fmt_children(node, ctx.indent(3))))

    @staticmethod
    def field(node: docutils.nodes.field, ctx: FormatContext) -> line_iterator:
        yield from chain(fmt_children(node, ctx))

    @staticmethod
    def field_list(node: docutils.nodes.field_list, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Structure.
    @staticmethod
    def transition(node: docutils.nodes.transition, ctx: FormatContext) -> line_iterator:
        yield "----"

    @staticmethod
    def paragraph(node: docutils.nodes.paragraph, ctx: FormatContext) -> line_iterator:
        yield from wrap_text(ctx.width, chain(fmt_children(node, ctx)))

    @staticmethod
    def title(node: docutils.nodes.title, ctx: FormatContext) -> line_iterator:
        text = " ".join(wrap_text(None, chain(fmt_children(node, ctx))))
        char = section_chars[ctx.section_depth - 1]
        if ctx.section_depth <= max_overline_depth:
            line = char * (len(text) + 2)
            yield line
            yield " " + text
            yield line
        else:
            yield text
            yield char * len(text)

    @staticmethod
    def block_quote(node: docutils.nodes.block_quote, ctx: FormatContext) -> line_iterator:
        yield from with_spaces(
            3, chain_intersperse("", fmt_children(node, ctx.indent(3))),
        )

    @staticmethod
    def directive(node: docutils.nodes.Node, ctx: FormatContext) -> line_iterator:
        d = node.attributes["directive"]

        yield " ".join([f".. {d.name}::", *d.arguments])
        # Just rely on the order being stable, hopefully.
        for k, v in d.options.items():
            yield f"   :{k}:" if v is None else f"   :{k}: {v}"

        if d.raw:
            yield from prepend_if_any("", with_spaces(3, d.content))
        else:
            sub_doc = parse_string("\n".join(d.content))
            if sub_doc.children:
                yield ""
                yield from with_spaces(3, fmt(sub_doc, ctx.indent(3)))

    @staticmethod
    def section(node: docutils.nodes.section, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx.in_section()))

    @staticmethod
    def document(node: docutils.nodes.document, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Tables.
    @staticmethod
    def row(node: docutils.nodes.row, ctx: FormatContext) -> line_iterator:
        all_lines = [
            chain_intersperse("", fmt_children(entry, ctx.with_width(w - 2)))
            for entry, w in zip(node.children, ctx.colwidths)
        ]
        for line_group in itertools.zip_longest(*all_lines):
            yield "|" + "|".join(
                " " + (line or "").ljust(w - 2) + " " for line, w in zip(line_group, ctx.colwidths)
            ) + "|"

    @staticmethod
    def tbody(node: docutils.nodes.tbody, ctx: FormatContext) -> line_iterator:
        sep = "+" + "+".join("-" * w for w in ctx.colwidths) + "+"
        yield from chain_intersperse(sep, fmt_children(node, ctx))

    thead = tbody

    @staticmethod
    def tgroup(node: docutils.nodes.tgroup, ctx: FormatContext) -> line_iterator:
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
    def table(node: docutils.nodes.table, ctx: FormatContext) -> line_iterator:
        yield from chain_intersperse("", fmt_children(node, ctx))

    # Admonitions.
    @staticmethod
    def admonition(node: docutils.nodes.admonition, ctx: FormatContext) -> line_iterator:
        title = node.children[0]
        assert isinstance(title, docutils.nodes.title)
        yield ".. admonition:: " + "".join(wrap_text(None, chain(fmt_children(title, ctx))))
        yield ""
        ctx = ctx.indent(3)
        yield from with_spaces(3, chain_intersperse("", (fmt(c, ctx) for c in node.children[1:])))

    @staticmethod
    def _sub_admonition(node: docutils.nodes.Node, ctx: FormatContext) -> line_iterator:
        yield f".. {node.tagname}::"
        yield ""
        yield from with_spaces(3, chain_intersperse("", fmt_children(node, ctx.indent(3))))

    attention = _sub_admonition
    caution = _sub_admonition
    danger = _sub_admonition
    error = _sub_admonition
    hint = _sub_admonition
    important = _sub_admonition
    note = _sub_admonition
    tip = _sub_admonition
    warning = _sub_admonition

    # Misc.
    @staticmethod
    def line(node: docutils.nodes.line, ctx: FormatContext) -> line_iterator:
        if not node.children:
            yield "|"
            return

        indent = 3 * ctx.line_block_depth
        ctx = ctx.indent(indent)
        prefix1 = "|" + " " * (indent - 1)
        prefix2 = " " * indent
        for first, line in enum_first(wrap_text(ctx.width, chain(fmt_children(node, ctx)))):
            yield (prefix1 if first else prefix2) + line

    @staticmethod
    def line_block(node: docutils.nodes.line_block, ctx: FormatContext) -> line_iterator:
        yield from chain(fmt_children(node, ctx.in_line_block()))

    @staticmethod
    def Text(node: docutils.nodes.Text, _: FormatContext) -> inline_iterator:
        # The rawsource attribute tends not to be set for text nodes not directly under paragraphs.
        if isinstance(node.parent, docutils.nodes.paragraph):
            # Any instance of "\ " disappears in the parsing. It may have an effect if it separates
            # this text from adjacent inline markup, but in that case it will be replaced by the
            # wrapping algorithm. Other backslashes may be unnecessary (e.g., "a\` b" or "a\b"), but
            # finding all of those is future work.
            yield node.rawsource.replace(r"\ ", "")
        else:
            yield node.astext()

    @staticmethod
    def reference(node: docutils.nodes.reference, ctx: FormatContext) -> inline_iterator:
        title = " ".join(wrap_text(None, chain(fmt_children(node, ctx))))
        anon_suffix: Callable[[bool], str] = lambda anonymous: "__" if anonymous else "_"
        attrs = node.attributes  # type: ignore
        children = node.children  # type: ignore

        # Handle references that are also substitution references.
        if len(children) == 1 and isinstance(children[0], docutils.nodes.substitution_reference):
            anonymous = bool(attrs.get("anonymous"))
            yield inline_markup(title + anon_suffix(anonymous))
            return

        # Handle references to external URIs. They can be either standalone hyperlinks, written as
        # just the URI, or an explicit "`text <url>`_" or "`text <url>`__".
        if "refuri" in attrs:
            uri = attrs["refuri"]
            if uri == title or uri == "mailto:" + title:
                yield inline_markup(title)
            else:
                anonymous = "target" not in attrs
                yield inline_markup(f"`{title} <{uri}>`{anon_suffix(anonymous)}")
            return

        # Simple reference names can consist of "alphanumerics plus isolated (no two adjacent)
        # internal hyphens, underscores, periods, colons and plus signs", according to
        # https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#reference-names.
        is_single_word = re.match("^[-_.:+a-zA-Z0-9]+$", title) and not re.search(
            "[-_.:+][-_.:+]", title
        )

        # "x__" is one of the few cases to trigger an explicit "anonymous" attribute (the other
        # being the similar "|x|__", which is already handled above).
        if "anonymous" in attrs:
            if not is_single_word:
                title = "`" + title + "`"
            yield inline_markup(title + anon_suffix(True))
            return

        anonymous = "target" not in attrs
        ref = attrs["refname"]
        # Check whether the reference name matches the text and can be made implicit. (Reference
        # names are case-insensitive.)
        if anonymous and ref.lower() == title.lower():
            if not is_single_word:
                title = "`" + title + "`"
            # "x_" is equivalent to "`x <x_>`__"; it's anonymous despite having a single underscore.
            yield inline_markup(title + anon_suffix(False))
        else:
            yield inline_markup(f"`{title} <{ref}_>`{anon_suffix(anonymous)}")

    @staticmethod
    def role(node: docutils.nodes.Node, ctx: FormatContext) -> inline_iterator:
        yield inline_markup(f":{node.attributes['role']}:`{node.attributes['text']}`")

    @staticmethod
    def ref_role(node: docutils.nodes.Node, ctx: FormatContext) -> inline_iterator:
        a = node.attributes
        target = a["target"]
        if a["has_explicit_title"]:
            title = a["title"].replace("<", r"\<")
            # TODO: This is a bit too broad, but not incorrect.
            title = title.replace("`", r"\`")
            text = f"{title} <{target}>"
        else:
            text = target
        yield inline_markup(f":{a['name']}:`{text}`")

    @staticmethod
    def inline(node: docutils.nodes.inline, ctx: FormatContext) -> inline_iterator:
        yield from chain(fmt_children(node, ctx))

    @staticmethod
    def target(node: docutils.nodes.target, ctx: FormatContext) -> line_iterator:
        if not isinstance(node.parent, (docutils.nodes.document, docutils.nodes.section)):
            return
        try:
            body = " " + node.attributes["refuri"]
        except KeyError:
            body = ""

        name = "_" if node.attributes.get("anonymous") else node.attributes["names"][0]
        yield f".. _{name}:{body}"

    @staticmethod
    def comment(node: docutils.nodes.comment, ctx: FormatContext) -> line_iterator:
        yield ".."
        if node.children:
            text = "\n".join(chain(fmt_children(node, ctx)))
            yield from with_spaces(3, text.split("\n"))

    @staticmethod
    def image(node: docutils.nodes.image, ctx: FormatContext) -> line_iterator:
        yield f".. image:: {node.attributes['uri']}"

    @staticmethod
    def literal_block(node: docutils.nodes.literal_block, ctx: FormatContext) -> line_iterator:
        langs = [c for c in node.attributes["classes"] if c != "code"]
        lang = langs[0] if langs else None
        yield ".. code::" + (" " + lang if lang else "")
        yield ""
        text = "".join(chain(fmt_children(node, ctx)))

        try:
            func = getattr(CodeFormatters, lang)
        except (AttributeError, TypeError):
            pass
        else:
            text = func(text)

        yield from with_spaces(3, text.split("\n"))


def fmt(node: docutils.nodes.Node, ctx: FormatContext) -> Iterator[str]:
    try:
        func = getattr(Formatters, type(node).__name__)
    except AttributeError:
        raise ValueError(f"Unknown node type {type(node).__name__}!")
    return func(node, ctx)  # type: ignore


def format_node(width: Optional[int], node: docutils.nodes.Node) -> str:
    if width is not None and width <= 0:
        width = None
    return "\n".join(fmt(node, FormatContext(0, width, "", [], 0))) + "\n"


def parse_string(s: str) -> docutils.nodes.document:
    parser = docutils.parsers.rst.Parser()
    settings = docutils.frontend.OptionParser(
        components=[docutils.parsers.rst.Parser]
    ).get_default_values()
    settings.report_level = docutils.utils.Reporter.SEVERE_LEVEL
    settings.halt_level = docutils.utils.Reporter.WARNING_LEVEL
    settings.file_insertion_enabled = False
    doc = docutils.utils.new_document("", settings=settings)
    doc.reporter = IgnoreMessagesReporter("", settings.report_level, settings.halt_level)
    parser.parse(s, doc)
    preproc(doc)

    return doc
