Change Log
==========

Unreleased
----------

**Added**

- Support for asynchronous functions.
- Ability to remove the blank line at the end of docstrings.

**Changed**

- Python file parsing now uses `libcst <https://libcst.readthedocs.io/en/latest>`_.
- When misformatted files are found, location info is printed with the line where the
  error is found if possible.

**Fixed**

- Bug where some raw docstrings were not being formatted.
- Bug where some syntax errors in python blocks were not caught or raised correctly.

1.0.2 (2020/12/27)
------------------

**Fixed**

- Fix UnicodeEncodeError in Windows Github Actions jobs.

1.0.1 (2020/12/27)
------------------

**Changed**

- Open files with ``UTF-8`` encoding.

**Fixed**

- Fix encoding/decoding errors when opening files on Windows.

1.0.0 (2020/12/26)
------------------

- First official docstrfmt release!

1.0.0.pre0 (2020/12/26)
-----------------------

- Forked from `dzhu/rstfmt <https://github.com/dzhu/rstfmt>`_
- Renamed to docstrfmt
- Added ability to format Python docstrings
- Switched to click for argument parsing
- Formatted code with black
- Made code easier to read
- Added more rst constructs
- Added more tests
