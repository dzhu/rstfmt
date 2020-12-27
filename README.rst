docstrfmt: a formatter for reStructuredText doc strings
=======================================================

.. image:: https://img.shields.io/pypi/v/docstrfmt.svg
    :alt: Latest docstrfmt Version
    :target: https://pypi.python.org/pypi/docstrfmt

.. image:: https://img.shields.io/pypi/pyversions/docstrfmt
    :alt: Supported Python Versions
    :target: https://pypi.python.org/pypi/docstrfmt

.. image:: https://img.shields.io/pypi/dm/docstrfmt
    :alt: PyPI - Downloads - Monthly
    :target: https://pypi.python.org/pypi/docstrfmt

.. image:: https://coveralls.io/repos/github/LilSpazJoekp/docstrfmt/badge.svg?branch=master
    :alt: Coveralls Coverage
    :target: https://coveralls.io/github/LilSpazJoekp/docstrfmt?branch=master

.. image:: https://github.com/LilSpazJoekp/docstrfmt/workflows/CI/badge.svg
    :alt: Github Actions Coverage
    :target: https://github.com/LilSpazJoekp/docstrfmt/actions?query=branch%3Amaster

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
    :alt: Contributor Covenant
    :target: https://github.com/LilSpazJoekp/docstrfmt/blob/master/CODE_OF_CONDUCT.md



*Strongly inspired by* rstfmt_ and rustfmt_.

*Highly experimental and unstable. Do not depend on this yet.*

Description
-----------

docstrfmt is a tool for automatically formatting reStructuredText_ in files and Python
docstrings in a consistent way.

Like Black_ and rstfmt_, the motivation is to provide a format that is reasonable and
minimally configurable to prevent teams from wasting time on style discussions (or
individuals on manually doing formatting, for that matter).

Currently, docstrfmt is in an early stage of development. The most common reST
constructs are covered but there are some that are not. If there is a construct missing
and would like to add it, feel free to open a PR to add it or open an issue and I'll see
what I can do.

To get a feel for the output of docstrfmt, see `the sample file <sample.rst>`__.

Differences between docstrfmt and rstfmt_
-----------------------------------------

The main difference between rstfmt_ and docstrfmt is the ability to format Python
docstrings. I am open to merging this project with rstfmt_, however there as several
differences in formatting conventions between the two (hence the separate fork).

Usage
-----

.. code-block:: sh

    # Install.
    pip install git+https://github.com/LilSpazJoekp/docstrfmt

    # Install from PyPI (but releases there may be out-of-date).
    pip install docstrfmt

    # Read a file from stdin and write the formatted version to stdout.
    docstrfmt

    # Format the given files in place.
    docstrfmt <file>...

    # Format the given files, printing all output to stdout.
    docstrfmt -o <file>...

    # Wrap paragraphs to the given line length (default 88).
    docstrfmt -l <length>

Like Black's blackd_, there is also a daemon that provides formatting via HTTP requests
to avoid the cost of starting and importing everything on every run.

.. code-block:: sh

    # Install.
    pip install https://github.com/LilSpazJoekp/docstrfmt[d]

    # Start the daemon (binds to localhost:5219 by default).
    docstrfmtd --bind-host=<host> --bind-port=<port>

    # Print the formatted version of a file.
    curl http://locahost:5219 --data-binary @<file>

    # Specify the line length (default 88).
    curl -H 'X-Line-Length: 72' http://locahost:5219 --data-binary @<file>

    # Mimic the standalone tool: read from stdin, write to stdout, exit with
    # a nonzero status code if there are errors.
    curl -fsS http://locahost:5219 --data-binary @/dev/stdin

With editors
~~~~~~~~~~~~

The default behavior of reading from stdin and writing to stdout should integrate well
with other systems, such as on-save hooks in editors. For example, here's a
configuration for reformatter.el_, including both standalone and daemon modes:

.. code-block:: lisp

    ;; Run the standalone tool.
    (reformatter-define docstrfmt
      :program "docstrfmt")
      :args '("-o" "-"))
    (add-hook 'rst-mode-hook #'docstrfmt-on-save-mode)

    ;; Query the daemon.
    (reformatter-define client-docstrfmt
      :program "curl"
      :args '("-fsS" "http://localhost:5219" "--data-binary" "@/dev/stdin"))
    (add-hook 'rst-mode-hook #'client-docstrfmt-on-save-mode)

.. _black: https://github.com/psf/black

.. _blackd: https://github.com/psf/black#blackd

.. _docutils: https://docutils.sourceforge.io/

.. _pandoc: https://pandoc.org/

.. _reformatter.el: https://github.com/purcell/reformatter.el

.. _restructuredtext: https://docutils.sourceforge.io/docs/user/rst/quickstart.html

.. _rustfmt: https://github.com/rust-lang/rustfmt
