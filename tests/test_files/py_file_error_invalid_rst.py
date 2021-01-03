"""This is an example python file"""


test = "value"


class ExampleClass:
    """Class docstring example

    .. codeblock:: python

        invalid

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

        self.test = "test"
        """Test attr docstring

        .. codeblock:: python

            print("Hello world")

        ..

        """

        self.test2 = "test"
        r"""Duis vel nulla ac risus semper fringilla vel non mauris. In :func:`elementum`\ s viverra
        arcu sed commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper
        eros ac gravida. Nam non ligula ipsum. Nam accumsan |subs|__ ex, nec |ultrices|
        est vestibulum__ in. Vestibulum vitae gravida lorem, vel laoreet lorem.

        .. |subs| replace:: ``SUBS``

        .. |ultrices| replace:: Really long text that needs wrapped. Duis vel nulla ac
            risus semper fringilla vel non mauris. In elementum viverra arcu sed
            commodo. In hac habitasse platea dictumst. Integer posuere ullamcorper eros
            ac gravida.

        """
