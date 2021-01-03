A ReStructuredText Primer
=========================

:Author: Richard Jones
:Version: $Revision: 5801 $
:Copyright: This document has been placed in the public domain.

.. contents::

The text below **contains** links that look like "(quickref__)". These are relative
links that point to the `Quick reStructuredText`_ user reference. If these links don't
work, please refer to the `master quick reference`_ document.

.. _master quick reference: http://docutils.sourceforge.net/docs/user/rst/quickref.html

.. _quick restructuredtext: quickref.html

- Test Author <test@example.com> `@TestAuthor <https://example.com/TestAuthor>`_

.. autosummary::

    test

.. note::

    This document is an informal introduction to reStructuredText. The `What Next?`_
    section below has links to further resources, including a formal reference.

.. _unused_ref:

Structure
---------

From the **outset**, let me say that "Structured Text" is probably a bit of a misnomer.
It's more like "Relaxed Text" that uses certain consistent patterns. These patterns are
interpreted by a HTML converter to produce "Very Structured Text" that can be used by a
web browser.

Title reference: `Title reference`

The most basic pattern recognised is a **paragraph** (quickref__). That's a chunk of
text that is separated by blank lines (one is enough). Paragraphs must have the same
indentation -- that is, line up at their left edge. Paragraphs that start indented will
result in indented quote paragraphs. For example:

.. code-block::

    This is a paragraph.  It's quite
    short.

       This paragraph will result in an indented block of
       text, typically used for quoting other text.

    This is another one.

Results in:

    This is a paragraph. It's quite short.

        This paragraph will result in an indented block of text, typically used for
        quoting other text.

    This is another one.

Text styles
-----------

(quickref__)

Inside paragraphs and other bodies of text, you may additionally mark text for *italics*
with "``*italics*``" or **bold** with "``**bold**``". This is called "inline markup".

If you want something to appear as a fixed-space literal, use "````double
back-quotes````". Note that no further fiddling is done inside the double back-quotes --
so asterisks "``*``" etc. are left alone.

If you find that you want to use one of the "special" characters in text, it will
generally be OK -- reStructuredText is pretty smart. For example, this lone asterisk *
is handled just fine, as is the asterisk in this equation: 5*6=30. If you actually want
text \*surrounded by asterisks* to **not** be italicised, then you need to indicate that
the asterisk is not special. You do this by placing a backslash just before it, like so
"``\*``" (quickref__), or by enclosing it in double back-quotes (inline literals), like
this:

.. code-block::

    ``*``

.. tip::

    Think of inline markup as a form of (parentheses) and use it the same way:
    immediately before and after the text being marked up. Inline markup by itself
    (surrounded by whitespace) or in the middle of a word won't be recognized. See the
    `markup spec`__ for full details.

Lists
~~~~~

Lists of items come in three main flavors: **enumerated**, **bulleted** and
**definitions**. In all list cases, you may have as many paragraphs, sublists, etc. as
you want, as long as the left-hand side of the paragraph or whatever aligns with the
first line of text in the list item.

Lists must always start a new paragraph -- that is, they must appear after a blank line.

**enumerated** lists (numbers, letters or roman numerals; quickref__)

    Start a line off with a number or letter followed by a period ".", right bracket ")"
    or surrounded by brackets "( )" -- whatever you're comfortable with. All of the
    following forms are recognised:

    .. code-block::

        1. numbers

        A. upper-case letters
           and it goes over many lines

           with two paragraphs and all!

        a. lower-case letters

           3. with a sub-list starting at a different number
           4. make sure the numbers are in the correct sequence though!

        I. upper-case roman numerals

        i. lower-case roman numerals

        (1) numbers again

        1) and again
        #. auto numbered

    Results in (note: the different enumerated list styles are not always supported by
    every web browser, so you may not get the full effect here):

    1. numbers

    A. upper-case letters and it goes over many lines

       with two paragraphs and all!

    a. lower-case letters

       3. with a sub-list starting at a different number
       4. make sure the numbers are in the correct sequence though!

    I. upper-case roman numerals

    i. lower-case roman numerals

    1. numbers again

    1. and again
    2. auto numbered

**bulleted** lists (quickref__)

    Just like enumerated lists, start the line off with a bullet point character -
    either "-", "+" or "*":

    .. code-block::

        * a bullet point using "*"

          - a sub-list using "-"

            + yet another sub-list

          - another item

    Results in all lists using ``-`` since all bullets are converted to ``-``:

    - a bullet point using "*"

      - a sub-list using "-"

        - yet another sub-list

      - another item

**definition** lists (quickref__)

    Unlike the other two, the definition lists consist of a term, and the definition of
    that term. The format of a definition list is:

    .. code-block::

        what
          Definition lists associate a term with a definition.

        *how*
          The term is a one-line phrase, and the definition is one or more
          paragraphs or body elements, indented relative to the term.
          Blank lines are not allowed between term and definition.

    Results in:

    what
        Definition lists associate a term with a definition.

    *how*
        The term is a one-line phrase, and the definition is one or more paragraphs or
        body elements, indented relative to the term. Blank lines are not allowed
        between term and definition.

Preformatting (code samples)
----------------------------

(quickref__)

To just include a chunk of preformatted, never-to-be-fiddled-with text, finish the prior
paragraph with "``::``". The preformatted block is finished when the text falls back to
the same indentation level as a paragraph prior to the preformatted block. For example:

.. code-block::

    An example::

        Whitespace, newlines, blank lines, and all kinds of markup
          (like *this* or \this) is preserved by literal blocks.
       Lookie here, I've dropped an indentation level
       (but not far enough)

    no more example

Results in:

    An example:

    .. code-block::

          Whitespace, newlines, blank lines, and all kinds of markup
            (like *this* or \this) is preserved by literal blocks.
        Lookie here, I've dropped an indentation level
        (but not far enough)

    no more example

Note that if a paragraph consists only of "``::``", then it's removed from the output:

.. code-block::

    ::

        This is preformatted text, and the
        last "::" paragraph is removed

Results in:

.. code-block::

    This is preformatted text, and the
    last "::" paragraph is removed

Python code blocks are formatted with Black_ (if it's found on ``PATH``).

.. code-block:: python

    x = [
        "here are some items",
        "indented and with line breaks",
        "the way Black does it",
    ]

.. code-block:: text

    this is just text

.. admonition:: title a b

    a
        b

    .. note::

        test

.. raw:: html

    <hr width=50 size=10>

.. image:: ../images/biohazard.png
    :alt: biohazard

.. figure:: ../images/biohazard.png
    :width: 200px
    :align: center
    :height: 100px
    :alt: alternate text
    :figclass: align-center

    figure are like images but with a caption

    and whatever else you wish to add

    .. code-block:: python

        import image

Math
~~~~

.. math::

    e^{\pi
    i}+1=0

:math:`\sum_{i=1}^\infty2^{-i}=1`

Auto documented blocks (Sphinx)
-------------------------------

.. automodule:: test
    :inherited-members:

Sections
--------

(quickref__)

To break longer text up into sections, you use **section headers**. These are a single
line of text (one or more words) with adornment: an underline alone, or an underline and
an overline together, in dashes "``-----``", equals "``======``", tildes "``~~~~~~``" or
any of the non-alphanumeric characters ``= - ` : ' " ~ ^ _ * + # < >`` that you feel
comfortable with. An underline-only adornment is distinct from an overline-and-underline
adornment using the same character. The underline/overline must be at least as long as
the title text. Be consistent, since all sections marked with the same adornment style
are deemed to be at the same level:

.. code-block::

    Chapter 1 Title
    ===============

    Section 1.1 Title
    -----------------

    Subsection 1.1.1 Title
    ~~~~~~~~~~~~~~~~~~~~~~

    Section 1.2 Title
    -----------------

    Chapter 2 Title
    ===============

This results in the following structure, illustrated by simplified pseudo-XML:

.. code-block::

    <section>
        <title>
            Chapter 1 Title
        <section>
            <title>
                Section 1.1 Title
            <section>
                <title>
                    Subsection 1.1.1 Title
        <section>
            <title>
                Section 1.2 Title
    <section>
        <title>
            Chapter 2 Title

(Pseudo-XML uses indentation for nesting and has no end-tags. It's not possible to show
actual processed output, as in the other examples, because sections cannot exist inside
block quotes. For a concrete example, compare the section structure of this document's
source text and processed output.)

Note that section headers are available as link targets, just using their name. To link
to the Lists_ heading, I write "``Lists_``". If the heading has a space in it like `text
styles`_, we need to quote the heading "```text styles`_``".

This is a separator.

----

Document Title / Subtitle
~~~~~~~~~~~~~~~~~~~~~~~~~

The title of the whole document is distinct from section titles and may be formatted
somewhat differently (e.g. the HTML writer by default shows it as a centered heading).

To indicate the document title in reStructuredText, use a unique adornment style at the
beginning of the document. To indicate the document subtitle, use another unique
adornment style immediately after the document title. For example:

.. code-block::

    ================
     Document Title
    ================
    ----------
     Subtitle
    ----------

    Section Title
    =============

    ...

Note that "Document Title" and "Section Title" above both use equals signs, but are
distict and unrelated styles. The text of overline-and-underlined titles (but not
underlined-only) may be inset for aesthetics.

Images
------

(quickref__)

To include an image in your document, you use the the ``image`` `test directive
<directive_>`__. For example:

.. code-block::

    .. image:: images/biohazard.png

results in:

.. image:: images/biohazard.png

The ``images/biohazard.png`` part indicates the filename of the image you wish to appear
in the document. There's no restriction placed on the image (format, size etc). If the
image is to appear in HTML and you wish to supply additional information, you may:

.. code-block::

    .. image:: images/biohazard.png
       :height: 100
       :width: 200
       :scale: 50
       :alt: alternate text

See the full `image directive documentation`__ for more info.

Substitution
------------

Duis vel nulla ac risus semper fringilla vel non mauris. In elementum viverra arcu sed
commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros ac gravida.
Nam non ligula ipsum. Nam accumsan |subs|__ ex, nec |ultrices| est vestibulum__ in.
Vestibulum vitae gravida lorem, vel laoreet lorem.

.. |subs| replace:: ``SUBS``

.. |ultrices| replace:: Really long text that needs wrapped. Duis vel nulla ac risus
    semper fringilla vel non mauris. In elementum viverra arcu sed commodo. In hac
    habitasse platea dictumst. Integer posuere ullamcorper eros ac gravida.

.. _reference_roles:

Ref Roles
---------

This is text with a ref role :func:`f`. This has :func:`f`\ s an ``s`` after it. This is
an :ref:`example explicit ref <reference_roles>` to this section. This is an `anonymous
link <http://example.com>`_

Line Blocks
-----------

|   a

|   a d b f

|   a
|   b
|   c d

|   a
|       b
|   c d

|   a
|       b
|           c
|               d

    |   a
    |       b
    |           c
    |               d

|

Tables
------

===== ===== ======
A     B     A or B
===== ===== ======
False False False
True  False True
False True  True
True  True  True
===== ===== ======

==== ==== ================================================
cell cell cell
==== ==== ================================================
cell cell Cell that has a lot of text and won't be wrapped
cell cell cell
cell cell cell
cell cell cell
==== ==== ================================================

==== ==== ==============================================================================
cell cell cell
==== ==== ==============================================================================
cell cell cell
cell cell cell that has a lot of text
cell cell cell that has a lot of text and won't be wrapped
cell cell cell that has a lot of text and should be wrapped because it is longer than 88
          characters
==== ==== ==============================================================================

===== ================ ==============
A     B                A or B
===== ================ ==============
False False            False
True  False            True
False True             True
True      True         has note block

      This has a list: .. note::

      - list item 1        Note
      - list item 2
      - list item 3
      - list item 4
===== ================ ==============

===== ============================= =====================================================================================================
A     B                             A or B
===== ============================= =====================================================================================================
False False                         False
True  False                         True
False True                          True
True      True                      has note block

      This has a list:              .. note::

      - list item 1                     Note
      - list item 2
      - list item 3
      - list item 4

      The next cell below is blank.
True                                .. code-block:: python

                                        print(
                                            "This code block is really long and wont be able to be wrapped in the default 88 characters."
                                        )
===== ============================= =====================================================================================================

Fields
------

:param test_param: param text
:param test_param: param text with note

    .. note::

        note


:returns: Return message

    .. note::

        note with code block

        .. code-block:: python

            print("Hello World!")


:raises: exception text

    .. note::

        note


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

What Next?
----------

.. seealso::

    Users who have questions or need assistance with Docutils or reStructuredText should
    post a message to the Docutils-users_ mailing list.

This primer introduces the most common features of reStructuredText, but there are a lot
more to explore. The `Quick reStructuredText`_ user reference is a good place to go
next. For complete details, the `reStructuredText Markup Specification`_ is the place to
go [1]_ .

.. [1] If that relative link doesn't work, try the master document:
    http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html.

.. _docutils project web site: http://docutils.sourceforge.net/

.. _docutils-users: ../mailing-lists.html#docutils-users

.. _restructuredtext markup specification: ../../ref/rst/restructuredtext.html
