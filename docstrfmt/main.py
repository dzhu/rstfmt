import contextlib
import glob
import sys
from ast import ClassDef, Constant, FunctionDef, get_source_segment, parse
from ast import walk as ast_walk
from os.path import abspath, basename
from pathlib import Path
from textwrap import dedent, indent
from typing import Any, List, Optional, Union

import click
from black import (
    PY36_VERSIONS,
    Mode,
    TargetVersion,
    find_pyproject_toml,
    parse_pyproject_toml,
)
from click import Context

from docstrfmt import Manager
from docstrfmt.const import __version__
from docstrfmt.util import get_code_line, plural

from . import debug


class Reporter:
    def __init__(self, current_level=1):
        self.current_level = current_level
        self.error_count = 0

    def _log_message(self, message, level, **formatting_kwargs):
        if self.current_level >= level:
            click.secho(message, **formatting_kwargs)

    def error(self, message, **formatting_kwargs):
        self.error_count += 1
        self._log_message(
            message, -1, bold=False, fg="red", err=True, **formatting_kwargs
        )

    def print(self, message, level=0, **formatting_kwargs):
        formatting_kwargs.setdefault("bold", level == 0)
        self._log_message(message, level, **formatting_kwargs)

    def debug(self, message, **formatting_kwargs):
        self._log_message(message, 3, bold=False, fg="blue", **formatting_kwargs)


# Define this here to support Python <3.7.
class nullcontext(contextlib.AbstractContextManager):  # type: ignore
    def __init__(self, enter_result: Any = None):
        self.enter_result = enter_result

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, *excinfo: Any) -> Any:
        pass


def parse_pyproject_config(
    context: click.Context, param: click.Parameter, value: Optional[str]
) -> Mode:
    if not value:
        pyproject_toml = find_pyproject_toml(tuple(context.params.get("files", ())))
        value = pyproject_toml if pyproject_toml else None
    if value:
        config = parse_pyproject_toml(value)
        config.pop("exclude", None)
        target_version = config.pop("target_version", PY36_VERSIONS)
        if target_version != PY36_VERSIONS:
            target_version = set(
                getattr(TargetVersion, version.upper())
                for version in target_version.split(",")
                if hasattr(TargetVersion, version.upper())
            )
        config["target_versions"] = target_version
        return Mode(**config)
    else:
        return Mode(line_length=88, target_versions=PY36_VERSIONS)


def parse_sources(context: click.Context, param: click.Parameter, value: Optional[str]):
    sources = value
    exclude = context.params.get("exclude", [])
    include_txt = context.params.get("include_txt", False)
    files_to_format = set()
    extensions = [".py", ".rst"] + ([".txt"] if include_txt else [])
    for source in sources:
        if source == "-":
            files_to_format.add(source)
        else:
            for item in glob.iglob(source, recursive=True):
                path = Path(item)
                if path.is_dir():
                    for file in [
                        found
                        for extension in extensions
                        for found in glob.iglob(
                            f"{path}/**/*{extension}", recursive=True
                        )
                    ]:
                        files_to_format.add(abspath(file))
                elif path.is_file():
                    files_to_format.add(abspath(item))
    for file in exclude:
        for f in glob.iglob(file, recursive=True):
            f = abspath(f)
            if f in files_to_format:
                files_to_format.remove(f)
    return sorted(list(files_to_format))


def _get_docstrings_from_node(source, node: Union[FunctionDef, ClassDef]):
    if not node.body:  # pragma: no cover
        return []
    nodes = []
    for body in node.body:
        if hasattr(body, "value"):
            body = body.value
            if isinstance(body, Constant) and isinstance(body.value, str):
                segment = get_source_segment(source, body, padded=True)
                if segment.strip().startswith('"""'):
                    nodes.append(segment)
    return nodes


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-p",
    "--pyproject_config",
    "mode",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=str,
    ),
    is_eager=True,
    callback=parse_pyproject_config,
    help="Path to pyproject.toml. Used to load black settings.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Log debugging information about each node being formatted. Can be specified multiple times for different levels of verbosity.",
)
@click.option(
    "-r",
    "--raw_input",
    type=str,
    help="Format the text passed in as a string. Outputs formatted text to stdout.",
)
@click.option(
    "-o", "--raw_output", is_flag=True, help="Output the formatted text to stdout."
)
@click.option(
    "-l",
    "--line-length",
    type=int,
    default=88,
    help="Wrap lines to the given line length where appropriate. Takes precedence over 'line_length' set in pyproject.toml if set.",
    show_default=True,
)
@click.option(
    "-t",
    "--file-type",
    type=click.Choice(["py", "rst"], case_sensitive=False),
    default="rst",
    help="Specify the raw input file type. Can only be used with -r.",
    show_default=True,
)
@click.option(
    "-c",
    "--check",
    is_flag=True,
    help="Check files and returns a non-zero code if files are not formatted correctly. Useful for linting.",
)
@click.option(
    "-T",
    "--include_txt",
    is_flag=True,
    help="Interpret *.txt files as reStructuredText and format them.",
)
@click.option(
    "-e",
    "--exclude",
    type=str,
    multiple=True,
    default=[
        "**/.direnv/",
        "**/.direnv/",
        "**/.eggs/",
        "**/.git/",
        "**/.hg/",
        "**/.mypy_cache/",
        "**/.nox/",
        "**/.tox/",
        "**/.venv/",
        "**/.svn/",
        "**/_build",
        "**/buck-out",
        "**/build",
        "**/dist",
    ],
    help="Path(s) to directories/files to exclude in formatting. Supports glob patterns.",
    show_default=True,
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Don't emit non-error messages to stderr. Errors are still emitted; silence those with 2>/dev/null. Overrides --verbose.",
)
@click.version_option(version=__version__)
@click.argument(
    "files",
    nargs=-1,
    type=str,
    callback=parse_sources,
)
@click.pass_context
def main(
    context: Context,
    mode: Mode,
    raw_input: str,
    raw_output: bool,
    verbose: int,
    line_length: int,
    file_type: str,
    check: bool,
    include_txt: bool,
    exclude: List[str],
    quiet: bool,
    files: List[str],
) -> None:
    reporter = Reporter(verbose)
    if quiet:
        reporter.current_level = -1
    manager = Manager(reporter, mode)
    misformatted = set()
    files_to_format = files

    if line_length != 88:
        mode.line_length = line_length

    line_length = mode.line_length
    for file in files_to_format:
        reporter.print(f"Checking {file}", 2)
        with nullcontext(sys.stdin) if file == "-" else open(file) as f:
            input_string = f.read()
        try:
            if file.endswith(".py") or (file_type == "py" and file == "-"):
                file_ast = parse(input_string, filename=basename(file))
                replacements = []
                current_class = ""
                for node in ast_walk(file_ast):
                    if isinstance(node, ClassDef):
                        current_class = node.name
                    if isinstance(node, (ClassDef, FunctionDef)):
                        if isinstance(node, ClassDef):
                            in_class = True
                        else:
                            in_class = False
                        doc_strings = _get_docstrings_from_node(input_string, node)
                        multiple_docstrings = len(doc_strings) > 1
                        for doc_string_num, doc_string in enumerate(doc_strings, 1):
                            node_name = (
                                f"{current_class}.{node.name}"
                                if current_class
                                else node.name
                            )
                            quotes = (
                                'r"""' if doc_string.lstrip().startswith("r") else '"""'
                            )
                            if "\n" not in doc_string:  # skip formatting if single line
                                continue
                            spaces = len(doc_string.split(quotes)[0])
                            source = (
                                dedent(doc_string)[:-3]
                                .strip()
                                .lstrip("r \n")
                                .lstrip('"')
                                .strip()
                            )
                            doc = manager.parse_string(source)
                            if verbose >= 3:
                                reporter.debug("=" * 60)
                                reporter.debug(debug.dump_node(doc))
                            width = line_length - spaces
                            if width < 1:
                                raise ValueError(
                                    f"Invalid starting width {line_length}"
                                )
                            output = manager.format_node(file, width, doc).rstrip()
                            if source == output:
                                reporter.print(
                                    f"Docstring{f' {doc_string_num}' if multiple_docstrings else ''} for {'class' if in_class else 'function'} {node.name if in_class else node_name!r} in file {file!r} is formatted correctly. Nice!",
                                    1,
                                )
                            else:
                                docstring_line = get_code_line(input_string, output)
                                misformatted.add(file)
                                reporter.print(
                                    f'Found incorrectly formatted docstring in {"class" if in_class else "function"} {node.name if in_class else node_name!r} in File "{file}", line {docstring_line}',
                                    1,
                                )
                                replacements.append(
                                    (
                                        doc_string,
                                        indent(
                                            f'{quotes}{output}\n\n"""', " " * spaces
                                        ),
                                    )
                                )
                if replacements:
                    if check:
                        reporter.print(f"File {file!r} could be reformatted.")
                    else:
                        for replacement in replacements:
                            input_string = input_string.replace(*replacement)
                        write_output(
                            file,
                            reporter,
                            input_string,
                            (
                                nullcontext(sys.stdout)
                                if file == "-" or raw_output
                                else open(file, "w")
                            ),
                            raw_output,
                        )
                elif raw_output:
                    write_output(
                        file,
                        reporter,
                        input_string,
                        (
                            nullcontext(sys.stdout)
                            if file == "-" or raw_output
                            else open(file, "w")
                        ),
                        raw_output,
                    )
            elif file.endswith(("rst", "txt") if include_txt else "rst") or file == "-":
                doc = manager.parse_string(input_string)
                if verbose >= 3:
                    reporter.debug("=" * 60)
                    reporter.debug(debug.dump_node(doc))
                output = manager.format_node(file, line_length, doc)
                if output != input_string:
                    misformatted.add(file)
                    if check:
                        reporter.print(f"File {file!r} could be reformatted.")
                    else:
                        write_output(
                            file,
                            reporter,
                            output,
                            (
                                nullcontext(sys.stdout)
                                if file == "-" or raw_output
                                else open(file, "w")
                            ),
                            raw_output,
                        )
                elif raw_output:
                    write_output(
                        file,
                        reporter,
                        input_string,
                        nullcontext(sys.stdout),
                        raw_input or raw_output,
                    )
        except Exception as error:
            reporter.error(f"{error.__class__.__name__}: {error}")
            reporter.print(f"Failed to format {file!r}")

    if misformatted:
        if check:
            reporter.print(
                f"{len(misformatted)} out of {plural('file', len(files_to_format))} could be reformatted."
            )
        else:
            reporter.print(
                f"{len(misformatted)} out of {plural('file', len(files_to_format))} were reformatted."
            )
    elif not raw_output:
        reporter.print(f"{plural('file', len(files_to_format))} were checked.")
    if reporter.error_count > 0:
        reporter.print(
            f"Done, but {plural('error', reporter.error_count)} occurred ❌💥❌"
        )
    elif not raw_output:
        reporter.print("Done! 🎉")
    if (check and misformatted) or reporter.error_count:
        context.exit(1)
    context.exit(0)


def write_output(file, log, output, output_manager, raw):
    with output_manager as f:
        f.write(output)
    if not raw:
        log.print(f"Reformatted {file!r}.")


if __name__ == "__main__":  # pragma: no cover
    main()
