##########################################
 rstfmt: a formatter for reStructuredText
##########################################

*Not to be confused with* rustfmt_.

*Highly experimental and unstable. Do not depend on this yet.*

*************
 Description
*************

rstfmt is a tool for automatically formatting reStructuredText_ files in
a consistent way.

Like Black_ and gofmt_, the motivation is to provide a format that is
reasonable and minimally configurable to prevent teams from wasting time
on style discussions (or individuals on manually doing formatting, for
that matter).

Currently, rstfmt is in an *extremely* early stage of development. Not
all reST constructs are covered and the interface or formatting may
change at any time without warning.

To get a feel for the output of rstfmt, see `the sample file
<sample.rst>`__.

*******
 Usage
*******

.. code:: sh

   # Install.
   pip install git+https://github.com/dzhu/rstfmt

   # Install from PyPI (but releases there may be out-of-date).
   pip install rstfmt

   # Read a file from stdin and write the formatted version to stdout.
   rstfmt

   # Format the given files, printing all output to stdout.
   rstfmt <file>...

   # Format the given files in place.
   rstfmt -i <file>...

   # Wrap paragraphs to the given line length (default 72).
   rstfmt -w <width>

Like Black's blackd_, there is also a daemon that provides formatting
via HTTP requests to avoid the cost of starting and importing everything
on every run.

.. code:: sh

   # Install.
   pip install https://github.com/dzhu/rstfmt[d]

   # Start the daemon (binds to localhost:5219 by default).
   rstfmtd --bind-host=<host> --bind-port=<port>

   # Print the formatted version of a file.
   curl http://locahost:5219 --data-binary @<file>

   # Specify the line length (default 72).
   curl -H 'X-Line-Length: 72' http://locahost:5219 --data-binary @<file>

   # Mimic the standalone tool: read from stdin, write to stdout, exit with
   # a nonzero status code if there are errors.
   curl -fsS http://locahost:5219 --data-binary @/dev/stdin

With editors
============

The default behavior of reading from stdin and writing to stdout should
integrate well with other systems, such as on-save hooks in editors. For
example, here's a configuration for reformatter.el_, including both
standalone and daemon modes:

.. code:: lisp

   ;; Run the standalone tool.
   (reformatter-define rstfmt
     :program "rstfmt")
   (add-hook 'rst-mode-hook #'rstfmt-on-save-mode)

   ;; Query the daemon.
   (reformatter-define client-rstfmt
     :program "curl"
     :args '("-fsS" "http://localhost:5219" "--data-binary" "@/dev/stdin"))
   (add-hook 'rst-mode-hook #'client-rstfmt-on-save-mode)

.. _black: https://github.com/psf/black

.. _blackd: https://github.com/psf/black#blackd

.. _docutils: https://docutils.sourceforge.io/

.. _gofmt: https://blog.golang.org/gofmt

.. _pandoc: https://pandoc.org/

.. _reformatter.el: https://github.com/purcell/reformatter.el

.. _restructuredtext: https://docutils.sourceforge.io/docs/user/rst/quickstart.html

.. _rustfmt: https://github.com/rust-lang/rustfmt
