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
    assert result.exit_code == 2
    assert (
        result.output
        == "Usage: main [OPTIONS] [FILES]...\nTry 'main -h' for help.\n\nError: Invalid value for '-l' / '--line-length': 3 is smaller than the minimum valid value 4.\n"
    )


@pytest.mark.parametrize(
    "file", ["tests/test_files/test_file.rst", "tests/test_files/py_file.py"]
)
def test_too_small_line_length(runner, file):
    args = ["-l", 4, file]
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
    args = [verbose, file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0

    file_path = os.path.abspath(file)
    suffix = f"{os.path.basename(file)}' is formatted correctly. Nice!\n1 file were checked.\nDone! 🎉\n"
    if file.endswith("rst"):
        results = [
            ("File '", suffix),
            (f"Checking {file_path}\nFile '", suffix),
        ]
    else:
        results = [
            ("Docstring for class 'ExampleClass' in file", suffix),
            (
                f"Checking {file_path}\nDocstring for class 'ExampleClass' in file",
                suffix,
            ),
        ]
    results.append(
        (
            f"Checking {file_path}\n============================================================\n- document",
            suffix,
        ),
    )
    level = verbose.count("v")
    startswith, endswith = results[level - 1]
    assert result.output.startswith(startswith)
    assert result.output.endswith(endswith)


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


def test_invalid_files(runner):
    args = ["-", "tests/test_files/test_file.rst"]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 2
    assert result.output == "ValueError: stdin can not be used with other paths\n"


@pytest.mark.parametrize("file", test_files)
def test_globbing(runner, file):
    args = [
        "-e",
        "tests/test_files/bad_table.rst",
        "-e",
        "tests/test_files/test_encoding.rst",
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
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", file_type, "-l", 80, "-"]
    result = runner.invoke(main, args=args, input=raw_file)
    assert result.exit_code == 0
    output = result.output
    result = runner.invoke(main, args=args, input=output)
    assert result.exit_code == 0
    assert result.output == output


@pytest.mark.parametrize(
    "file,file_type",
    [("tests/test_files/test_file.rst", "rst"), ("tests/test_files/py_file.py", "py")],
)
def test_raw_input(runner, file, file_type):
    with open(file, encoding="utf-8") as f:
        raw_file = f.read()
    args = ["-t", file_type, "-l", 80, "-r", raw_file]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    args[-1] = output = result.output
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert result.output == output


def test_encoding(runner):
    file = "tests/test_files/test_encoding.rst"
    args = [file]
    result = runner.invoke(main, args=args)
    assert result.output == "1 file were checked.\nDone! 🎉\n"
    assert result.exit_code == 0


def test_encoding_raw_input(runner):
    file = ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    args = ["-r", file]
    result = runner.invoke(main, args=args)
    assert result.output == file
    assert result.exit_code == 0


def test_encoding_raw_output(runner):
    file = "tests/test_files/test_encoding.rst"
    args = ["-o", file]
    result = runner.invoke(main, args=args)
    assert (
        result.output
        == ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    )
    assert result.exit_code == 0


def test_encoding_stdin(runner):
    file = ".. note::\n\n    á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì Ì î Î ï Ï ñ Ñ ó Ó ò Ò ô Ô ö Ö.\n    õ Õ ø Ø œ Œ ß ú Ú ù Ù û Û ü Ü á Á à À â Â ä Ä ã Ã å Å æ Æ ç Ç é É è È ê Ê ë Ë í Í ì.\n"
    args = ["-"]
    result = runner.invoke(main, args=args, input=file)
    assert result.output == file
    assert result.exit_code == 0
