docstrfmt Formatting Sample
===========================

(The purpose of this file is to demonstrate formatting at the reST level, so find a raw
version if you're seeing this rendered.)

Section headers
---------------

The lengths of the section header lines are fixed to match the title text, whether
they're too long or too short in the input. (They do have to be at least four
characters, though, or they won't even be parsed as section headers.)

Subsections
~~~~~~~~~~~

Subsubsections
++++++++++++++

Subsubsubsections
.................

Subsubsubsubsections
''''''''''''''''''''

Substitution
""""""""""""

Duis vel nulla ac risus semper fringilla vel non mauris. In elementum viverra arcu sed
commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros ac gravida.
Nam non ligula ipsum. Nam accumsan |subs|__ ex, nec |ultrices| est vestibulum__ in.
Vestibulum vitae gravida lorem, vel laoreet lorem.

.. |subs| replace:: ``SUBS``

.. |ultrices| replace:: Really long text that needs wrapped. Duis vel nulla ac risus
    semper fringilla vel non mauris. In elementum viverra arcu sed commodo. In hac
    habitasse platea dictumst. Integer posuere ullamcorper eros ac gravida.

Wrapping
--------

Paragraphs are wrapped to fit within the specified line length.

Duis vel nulla ac risus semper fringilla vel non mauris. In elementum viverra arcu sed
commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros ac gravida.
Nam non ligula ipsum. Nam accumsan ornare ex, nec ultrices est vestibulum in. Vestibulum
vitae gravida lorem, vel laoreet lorem.

Indentation
-----------

All indentation is done three spaces at a time. This may look a bit odd for bulleted
lists in isolation, but it makes everything consistent.

.. note::

    - Thing 1

      1. Thing 2
      2. Thing 3

    - term
          definition

          - |   I have eaten
            |   the red wheel
            |   barrow

Lists
-----

Lists of items with no blocks will have no empty lines between them.

- Interdum et malesuada fames ac ante ipsum primis in faucibus.
- Vestibulum placerat ipsum tortor, sit amet elementum leo fringilla et. Nunc eu
  efficitur massa.
- Morbi placerat sagittis enim a placerat.
- Proin blandit imperdiet tristique.
- Donec consectetur vel magna in molestie. Etiam mollis leo mi, eget fermentum justo
  commodo vel.

If any item has any blocks, empty lines are added between all items.

- Vestibulum finibus volutpat nunc. Aliquam sed purus luctus, rutrum nulla nec,
  scelerisque dolor. Integer tempor placerat nunc in rutrum. Praesent blandit nulla in
  sagittis porta. Donec sed odio volutpat, venenatis augue ac, suscipit libero. Nullam
  eu lacinia quam.

  .. note::

      This is a note.

- Vivamus eu risus eget nisi pharetra dictum gravida quis felis.
- Morbi quis iaculis velit, non dictum lectus. Duis vitae ullamcorper orci, a ornare
  nunc.
- Etiam consectetur facilisis ligula, in convallis elit consequat non. Integer varius
  turpis sagittis odio elementum tristique. Praesent at sollicitudin metus, vel cursus
  sapien. Suspendisse augue lorem, tempus id tortor ut, porttitor tristique ante. Fusce
  non felis hendrerit, gravida sem vitae, elementum diam. Nunc ultrices arcu tincidunt,
  tincidunt erat nec, finibus purus.

Enumerated lists are always auto-enumerated.

Code
----

Python code blocks are formatted with Black_ and Go ones with gofmt_ (if it's found on
``PATH``).

.. code-block:: python

    x = [
        "here are some items",
        "indented and with line breaks",
        "the way Black does it",
    ]

Comments
--------

..
    Comments       are preserved
         with
      exactly     whatever  formatting
    they had in

     the    input.

          Formatting them
        is up
      to
    you.

    (Trailing spaces are still removed, since that happens early in the
    reST parser.)

Tables
------

Here's a grid table followed by a simple table:

===== ===== ======
A     B     A or B
===== ===== ======
False False False
True  False True
False True  True
True  True  True
===== ===== ======

Thanks
------

Lorem ipsum text provided by https://www.lipsum.com.

.. _black: https://github.com/psf/black

.. _gofmt: https://blog.golang.org/gofmt
