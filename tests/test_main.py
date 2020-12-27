import os
import shutil

import pytest
from click.testing import CliRunner

from docstrfmt.main import main

test_files = [
    "tests/test_files",
    "**/*.rst",
    "**/*.py",
    "tests/test_files/test_file.rst",
    "tests/test_files/py_file.py",
]

test_line_length = [13, 34, 55, 72, 89, 144]


@pytest.fixture
def runner():
    runner = CliRunner()
    files_to_copy = os.path.abspath("tests/test_files")
    with runner.isolated_filesystem() as temp_dir:
        shutil.copytree(files_to_copy, f"{temp_dir}/tests/test_files")
        yield runner


@pytest.mark.parametrize("length", test_line_length)
@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_line_length(runner, length, file):
    args = ["-l", length, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_invalid_line_length(runner, file):
    args = ["-l", 3, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.startswith("ValueError: Invalid starting width")


def test_pyproject_toml(runner):
    args = ["-p", "tests/test_files/pyproject.toml", "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.endswith("checked.\nDone! 🎉\n")


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_raw_output(runner, file):
    args = ["-o", file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    if file.endswith("rst"):
        assert result.output.startswith("A ReStructuredText Primer")
    elif file.endswith("py"):
        assert result.output.startswith('"""This is an example python file"""')
    output = result.output
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == output


@pytest.mark.parametrize("verbose", ["-v", "-vv", "-vvv"])
@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_verbose(runner, verbose, file):
    args = ["-l", 88, verbose, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0

    if file.endswith("rst"):
        results = [
            "1 file were checked.\nDone! 🎉\n",
            f"Checking {os.path.abspath(file)}\n1 file were checked.\nDone! 🎉\n",
        ]
    else:
        results = [
            "Docstring for class 'ExampleClass' in file",
            f"Checking {os.path.abspath(file)}\nDocstring for class 'ExampleClass' in file",
        ]
    results.append(
        f"Checking {os.path.abspath(file)}\n============================================================\n- document",
    )
    level = verbose.count("v")
    assert result.output.startswith(results[level - 1])


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_check(runner, file):
    args = ["-c", "-l", 80, os.path.abspath(file)]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 1
    assert result.output.endswith(
        "could be reformatted.\n1 out of 1 file could be reformatted.\nDone! 🎉\n"
    )


def test_include_txt(runner):
    args = ["-l", 80, "-T", "tests/test_files/test_file.txt"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output.startswith("Reformatted")


def test_exclude(runner):
    args = ["-e", "tests/test_files/test_file.rst", "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == "0 files were checked.\nDone! 🎉\n"


def test_quiet(runner):
    args = ["-q", "-l", 80, "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.parametrize("file", test_files)
def test_globbing(runner, file):
    args = [
        "-e",
        "tests/test_files/bad_table.rst",
        "-e",
        "tests/test_files/test_errors.rst",
        "-l",
        80,
        file,
    ]
    result = runner.invoke(main, args=args)
    assert result.output.startswith("Reformatted")
    assert result.exit_code == 0


def test_bad_table(runner):
    file = "tests/test_files/bad_table.rst"
    args = ["-l", 80, file]
    result = runner.invoke(main, args=args)
    assert result.output.startswith(
        "NotImplementedError: Tables with cells that span "
        "multiple cells are not supported. Consider using "
        "the 'include' directive to include the table from "
        f"another file.\nFailed to format {os.path.abspath(file)!r}"
    )
    assert result.output.endswith(
        """1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"""
    )
    assert result.exit_code == 1


def test_bad_code_block(runner):
    file = "tests/test_files/test_errors.rst"
    args = ["-l", 80, file]
    result = runner.invoke(main, args=args)
    assert result.output.startswith(
        f"SyntaxError: EOL while scanning string literal:\n"
        f'\nFile "{os.path.abspath(file)}", line 3:'
    )
    assert result.output.endswith(
        """1 file were checked.\nDone, but 1 error occurred ❌💥❌\n"""
    )
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "file,file_type",
    [("tests/test_files/test_file.rst", "rst"), ("tests/test_files/py_file.py", "py")],
)
def test_stdin(runner, file, file_type):
    with open(file) as f:
        raw_file = f.read()
    args = ["-t", file_type, "-l", 80, "-"]
    result = runner.invoke(main, args=args, input=raw_file)
    assert result.exit_code == 0
    if file_type == "rst":
        assert result.output.startswith("A ReStructuredText Primer")
    else:
        assert result.output.startswith('"""This is an example python file"""')
    endswith = "Reformatted '-'.\n1 out of 1 file were reformatted.\nDone! 🎉\n"
    assert result.output.endswith(endswith)
    output = result.output.split(endswith)[0]
    result = runner.invoke(main, args=args, input=output)
    assert result.exit_code == 0
    assert result.output == "1 file were checked.\nDone! 🎉\n"
