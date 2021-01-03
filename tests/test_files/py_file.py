"""This is an example python file"""


test = "value"


class ExampleClass:
    """Class docstring example

    Test table

    ===== ================ ======================================================================================================
    A     B                A or B
    ===== ================ ======================================================================================================
    False False            False
    True  False            True
    False True             True
    True      True         has note block

          This has a list: .. note::

          - list item 1        Note
          - list item 2
          - list item 3
          - list item 4
    True                   .. code-block:: python

                               print(
                                   "This code block is really long and won't be able to be wrapped in the default 88 characters."
                               )
    ===== ================ ======================================================================================================

    """

    def __init__(self, *args, **kwargs):
        """First doc str"""

        self.test = "value"
        """Test attr docstring

        .. code-block:: python

            print("Hello world")

        ..

        """

        self.test2 = "value"
        r"""Duis :func:`elementum`\ s ac |subs|__ ex, nec |ultrices| est vestibulum__.

        .. |subs| replace:: ``SUBS``

        .. |ultrices| replace:: Really long text that needs wrapped. Duis vel nulla ac
            risus semper fringilla vel non mauris. In elementum viverra arcu sed
            commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros
            ac gravida.

        """
