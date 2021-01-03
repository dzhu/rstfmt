import contextlib
import glob
import sys
from copy import copy
from os.path import abspath, basename
from pathlib import Path
from textwrap import dedent, indent
from typing import TYPE_CHECKING, Any, List, Optional

import click
import libcst as cst
from black import (
    PY36_VERSIONS,
    Mode,
    TargetVersion,
    find_pyproject_toml,
    parse_pyproject_toml,
)
from click import Context
from libcst import CSTTransformer, Expr
from libcst.metadata import ParentNodeProvider, PositionProvider

from docstrfmt.const import __version__
from docstrfmt.debug import dump_node
from docstrfmt.docstrfmt import Manager
from docstrfmt.exceptions import InvalidRstErrors
from docstrfmt.util import plural

if TYPE_CHECKING:  # pragma: no cover
    from libcst import AssignTarget, ClassDef, FunctionDef, Module, SimpleString


class Reporter:
    def __init__(self, level=1):
        self.level = level
        self.error_count = 0

    def _log_message(self, message, level, **formatting_kwargs):
        if self.level >= level:
            click.secho(message, err=True, **formatting_kwargs)

    def debug(self, message, **formatting_kwargs):
        self._log_message(message, 3, bold=False, fg="blue", **formatting_kwargs)

    def error(self, message, **formatting_kwargs):
        self.error_count += 1
        self._log_message(message, -1, bold=False, fg="red", **formatting_kwargs)

    def print(self, message, level=0, **formatting_kwargs):
        formatting_kwargs.setdefault("bold", level == 0)
        self._log_message(message, level, **formatting_kwargs)


# Define this here to support Python <3.7.
class nullcontext(contextlib.AbstractContextManager):  # type: ignore
    def __init__(self, enter_result: Any = None):
        self.enter_result = enter_result

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, *excinfo: Any) -> Any:
        pass


class Visitor(CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

    def __init__(self, object_name, file, line_length, manager):
        super().__init__()
        self._last_assign = None
        self._object_names = [object_name]
        self._object_type = None
        self._blank_line = manager.docstring_trailing_line
        self.file = file
        self.line_length = line_length
        self.manager = manager
        self.misformatted = False

    def _is_docstring(self, node: "SimpleString") -> bool:
        return node.quote.startswith(('"""', "'''")) and isinstance(
            self.get_metadata(ParentNodeProvider, node), Expr
        )

    def leave_ClassDef(self, original_node: "ClassDef", updated_node: "ClassDef"):
        self._object_names.pop(-1)
        return updated_node

    def leave_FunctionDef(
        self, original_node: "FunctionDef", updated_node: "FunctionDef"
    ):
        self._object_names.pop(-1)
        return updated_node

    def leave_SimpleString(
        self, original_node: "SimpleString", updated_node: "SimpleString"
    ):
        if self._is_docstring(original_node):
            position_meta = self.get_metadata(PositionProvider, original_node)
            if self._last_assign:
                self._object_names.append(self._last_assign.target.children[2].value)
                old_object_type = copy(self._object_type)
                self._object_type = "attribute"
            indent_level = position_meta.start.column
            source = dedent(
                (" " * indent_level) + original_node.evaluated_value
            ).rstrip()
            doc = self.manager.parse_string(self.file, source)
            if self.manager.reporter.level >= 3:
                self.manager.reporter.debug("=" * 60)
                self.manager.reporter.debug(dump_node(doc))
            width = self.line_length - indent_level
            if width < 1:
                raise ValueError(f"Invalid starting width {self.line_length}")
            output = self.manager.format_node(width, doc, True).rstrip()
            object_display_name = (
                f'{self._object_type} {".".join(self._object_names)!r}'
            )
            single_line = len(output.splitlines()) == 1
            original_strip = original_node.evaluated_value.rstrip(" ")
            end_line_count = len(original_strip) - len(original_strip.rstrip("\n"))
            ending = "" if single_line else "\n\n" if self._blank_line else "\n"
            if single_line:
                correct_ending = 0 == end_line_count
            else:
                correct_ending = int(self._blank_line) + 1 == end_line_count
            if source == output and correct_ending:
                self.manager.reporter.print(
                    f"Docstring for {object_display_name} in file {self.file!r} is formatted correctly. Nice!",
                    1,
                )
            else:
                self.misformatted = True
                file_link = f'File "{self.file}"'
                self.manager.reporter.print(
                    f"Found incorrectly formatted docstring. Docstring for {object_display_name} in {file_link}.",
                    1,
                )
                value = indent(
                    f'{original_node.prefix}"""{output}{ending}"""', " " * indent_level
                ).lstrip()
                updated_node = updated_node.with_changes(value=value)
            if self._last_assign:
                self._last_assign = None
                self._object_names.pop(-1)
                self._object_type = old_object_type
        return updated_node

    def visit_AssignTarget_target(self, node: "AssignTarget") -> None:
        self._last_assign = node

    def visit_ClassDef(self, node: "ClassDef") -> Optional[bool]:
        self._object_names.append(node.name.value)
        self._object_type = "class"
        self._last_assign = None
        return True

    def visit_FunctionDef(self, node: "FunctionDef") -> Optional[bool]:
        self._object_names.append(node.name.value)
        self._object_type = "function"
        self._last_assign = None
        return True

    def visit_Module(self, node: "Module") -> Optional[bool]:
        self._object_type = "module"
        return True


def _parse_pyproject_config(
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


def _parse_sources(
    context: click.Context, param: click.Parameter, value: Optional[str]
):
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


def _process_python(
    check, file, input_string, line_length, manager, misformatted, raw_output
):
    filename = basename(file)
    object_name = filename.split(".")[0]
    visitor = Visitor(object_name, file, line_length, manager)
    module = cst.parse_module(input_string)
    wrapper = cst.MetadataWrapper(module)
    result = wrapper.visit(visitor)
    if visitor.misformatted:
        misformatted.add(file)
        if check and not raw_output:
            manager.reporter.print(f"File {file!r} could be reformatted.")
        else:
            _write_output(
                file,
                manager.reporter,
                result.code,
                (
                    nullcontext(sys.stdout)
                    if file == "-" or raw_output
                    else open(file, "w", encoding="utf-8")
                ),
                raw_output,
            )
    elif raw_output:
        _write_output(
            file, manager.reporter, input_string, nullcontext(sys.stdout), raw_output
        )
    return misformatted


def _process_rst(
    check, file, input_string, line_length, manager, misformatted, raw_output
):
    doc = manager.parse_string(file, input_string)
    if manager.reporter.level >= 3:
        manager.reporter.debug("=" * 60)
        manager.reporter.debug(dump_node(doc))
    output = manager.format_node(line_length, doc)
    if output == input_string:
        manager.reporter.print(f"File {file!r} is formatted correctly. Nice!", 1)
        if raw_output:
            _write_output(
                file,
                manager.reporter,
                input_string,
                nullcontext(sys.stdout),
                raw_output,
            )
            return misformatted
    else:
        misformatted.add(file)
        if check and not raw_output:
            manager.reporter.print(f"File {file!r} could be reformatted.")
        else:
            _write_output(
                file,
                manager.reporter,
                output,
                (
                    nullcontext(sys.stdout)
                    if file == "-" or raw_output
                    else open(file, "w", encoding="utf-8")
                ),
                raw_output,
            )
    return misformatted


def _write_output(file, reporter, output, output_manager, raw):
    with output_manager as f:
        f.write(output)
    if not raw:
        reporter.print(f"Reformatted {file!r}.")


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
    callback=_parse_pyproject_config,
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
    "--raw-input",
    type=str,
    help="Format the text passed in as a string. Formatted text will be output to stdout.",
)
@click.option(
    "-o", "--raw_output", is_flag=True, help="Output the formatted text to stdout."
)
@click.option(
    "-l",
    "--line-length",
    type=click.IntRange(4),
    default=88,
    help="Wrap lines to the given line length where possible. Takes precedence over 'line_length' set in pyproject.toml if set.",
    show_default=True,
)
@click.option(
    "-t",
    "--file-type",
    type=click.Choice(["py", "rst"], case_sensitive=False),
    default="rst",
    help="Specify the raw input file type. Can only be used with --raw-input or stdin.",
    show_default=True,
)
@click.option(
    "-c",
    "--check",
    is_flag=True,
    help="Check files and returns a non-zero code if files are not formatted correctly. Useful for linting. Ignored if raw-input, raw-output, stdin is used.",
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
@click.option(
    "--docstring-trailing-line/--no-docstring-trailing-line",
    default=True,
    help="Whether or not to add a blank line at the end of docstrings.",
)
@click.version_option(version=__version__)
@click.argument(
    "files",
    nargs=-1,
    type=str,
    callback=_parse_sources,
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
    docstring_trailing_line: bool,
    files: List[str],
) -> None:
    reporter = Reporter(verbose)
    if "-" in files and len(files) > 1:
        reporter.error("ValueError: stdin can not be used with other paths")
        context.exit(2)
    if quiet or raw_output or files == ["-"]:
        reporter.level = -1
    manager = Manager(reporter, mode, docstring_trailing_line)
    misformatted = set()

    if line_length != 88:
        mode.line_length = line_length

    if raw_input:
        file = "<raw_input>"
        check = False
        try:
            if file_type == "py":
                misformatted = _process_python(
                    check, file, raw_input, line_length, manager, misformatted, True
                )
            elif file_type == "rst":
                misformatted = _process_rst(
                    check, file, raw_input, line_length, manager, misformatted, True
                )
        except InvalidRstErrors as errors:
            reporter.error(str(errors))
            context.exit(1)

        context.exit(0)
    line_length = mode.line_length
    for file in files:
        if file == "-":
            raw_output = True
        reporter.print(f"Checking {file}", 2)
        with nullcontext(sys.stdin) if file == "-" else open(
            file, encoding="utf-8"
        ) as f:
            input_string = f.read()
        try:
            if file.endswith(".py") or (file_type == "py" and file == "-"):
                misformatted = _process_python(
                    check,
                    file,
                    input_string,
                    line_length,
                    manager,
                    misformatted,
                    raw_output,
                )
            elif file.endswith(("rst", "txt") if include_txt else "rst") or file == "-":
                misformatted = _process_rst(
                    check,
                    file,
                    input_string,
                    line_length,
                    manager,
                    misformatted,
                    raw_output,
                )
        except InvalidRstErrors as errors:
            reporter.error(str(errors))
            reporter.print(f"Failed to format {file!r}")
        except Exception as error:
            reporter.error(f"{error.__class__.__name__}: {error}")
            reporter.print(f"Failed to format {file!r}")

    if misformatted and not raw_output:
        if check:
            reporter.print(
                f"{len(misformatted)} out of {plural('file', len(files))} could be reformatted."
            )
        else:
            reporter.print(
                f"{len(misformatted)} out of {plural('file', len(files))} were reformatted."
            )
    elif not raw_output:
        reporter.print(f"{plural('file', len(files))} were checked.")
    if reporter.error_count > 0:
        reporter.print(
            f"Done, but {plural('error', reporter.error_count)} occurred ❌💥❌"
        )
    elif not raw_output:
        reporter.print("Done! 🎉")
    if (check and misformatted) or reporter.error_count:
        context.exit(1)
    context.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
