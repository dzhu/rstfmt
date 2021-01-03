from docutils.parsers.rst.states import ParserError
from docutils.utils import roman


def get_code_line(current_source, code):
    lines = current_source.splitlines()
    code_lines = code.splitlines()
    multiple = len([line for line in lines if code_lines[0] in line]) > 1
    for line_number, line in enumerate(lines, 1):
        if code_lines[0] in line:
            if multiple:
                for offset, sub_line in enumerate(code_lines):
                    if sub_line not in lines[line_number - 1 + offset]:
                        break
                else:
                    return line_number
            else:
                return line_number


# Modified from docutils.parsers.rst.states.Body
def make_enumerator(ordinal, sequence, format):
    """Construct and return the next enumerated list item marker, and an auto-enumerator
    ("#" instead of the regular enumerator).

    Return ``None`` for invalid (out of range) ordinals.

    """
    if sequence == "#":  # pragma: no cover
        enumerator = "#"
    elif sequence == "arabic":
        enumerator = str(ordinal)
    else:
        if sequence.endswith("alpha"):
            if ordinal > 26:  # pragma: no cover
                return None
            enumerator = chr(ordinal + ord("a") - 1)
        elif sequence.endswith("roman"):
            try:
                enumerator = roman.toRoman(ordinal)
            except roman.RomanError:  # pragma: no cover
                return None
        else:  # pragma: no cover
            raise ParserError(f'unknown enumerator sequence: "{sequence}"')
        if sequence.startswith("lower"):
            enumerator = enumerator.lower()
        elif sequence.startswith("upper"):
            enumerator = enumerator.upper()
        else:  # pragma: no cover
            raise ParserError(f'unknown enumerator sequence: "{sequence}"')
    next_enumerator = format[0] + enumerator + format[1]
    return next_enumerator


def plural(word, count, thousands_separator=True):
    if count == 1:
        s = False
    else:
        s = True
    count_str = f"{count:,}" if thousands_separator else str(count)
    return f"{count_str} {word}s" if s else f"{count_str} {word}"
