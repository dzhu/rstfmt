import argparse
import contextlib
import sys
import warnings
from typing import Any, ContextManager, TextIO, cast

from . import debug, rst_extras, rstfmt


# Define this here to support Python <3.7.
class nullcontext(contextlib.AbstractContextManager):  # type: ignore
    def __init__(self, enter_result: Any = None):
        self.enter_result = enter_result

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, *excinfo: Any) -> Any:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in-place", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-w", "--width", type=int, default=72)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    rst_extras.register()

    STDIN = "-"

    for fn in args.files or [STDIN]:
        cm = cast(ContextManager[TextIO], nullcontext(sys.stdin) if fn == STDIN else open(fn))

        with cm as f:
            doc = rstfmt.parse_string(f.read())

        if args.verbose:
            print("=" * 60, fn, file=sys.stderr)
            debug.dump_node(doc, sys.stderr)

        if args.test:
            try:
                debug.run_test(doc)
            except AssertionError as e:
                raise AssertionError(f"Failed consistency test on {fn}!") from e

        output = rstfmt.format_node(args.width, doc)

        if fn != STDIN and args.in_place:
            cm = open(fn, "w")
        else:
            cm = nullcontext(sys.stdout)
            if fn == STDIN and args.in_place:
                warnings.warn("Cannot edit stdin in place; writing to stdout!")

        with cm as f:
            f.write(output)


if __name__ == "__main__":
    main()
