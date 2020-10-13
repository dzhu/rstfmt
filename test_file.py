"""Provide CommentForest for Submission comments."""
from heapq import heappop, heappush
from typing import TYPE_CHECKING, List, Optional, Union

from praw.exceptions import DuplicateReplaceException
from praw.models import MoreComments

if TYPE_CHECKING:  # pragma: no cover
    from praw.reddit.comment import Comment  # noqa: F401
    from praw.reddit.submission import Submission


class CommentForest:

    def replace_more(self, limit: int = 32, threshold: int = 0) -> List["MoreComments"]:
        """Update the comment forest by resolving instances of MoreComments.

        :param limit: The maximum number of :class:`.MoreComments` instances to replace.
            Each replacement requires 1 API request. Set to ``None`` to have no limit,
            or to ``0`` to remove all :class:`.MoreComments` instances without
            additional requests (default: 32).

            this is a separate sentence.
        :param threshold: The minimum number of children comments a
            :class:`.MoreComments` instance must have in order to be replaced.
            :class:`.MoreComments` instances that represent "continue this thread" links
            unfortunately appear to have 0 children. (default: 0).
        :returns: A list of :class:`.MoreComments` instances that were not replaced.

        For example, to replace up to 32 :class:`.MoreComments` instances of a
        submission try:

        .. code-block:: python

            submission = reddit.submission(
                '3hahrw'
            )
            submission.comments.replace_more()

        Alternatively, to replace :class:`.MoreComments` instances within the replies of
        a single comment try:

        .. code-block:: python

            comment = reddit.comment(
            "d8r4im1"
            )
            comment.refresh()
            comment.replies.replace_more()

        .. note::

            This method can take a long time as each replacement will discover at most
            20 new :class:`.Comment` or :class:`.MoreComments` instances. As a result,
            consider looping and handling exceptions until the method returns
            successfully. For example:

            .. code-block:: python

                while True:
                    try:
                        submission.comments.replace_more()
                        break
                    except PossibleExceptions:
                        print("Handling replace_more exception")
                        sleep(1)

        .. warning::

            If this method is called, and the comments are refreshed, calling this
            method again will result in a :class:`.DuplicateReplaceException`.

        """
        remaining = limit
        more_comments = self._gather_more_comments(self._comments)
        skipped = []

        # Fetch largest more_comments until reaching the limit or the threshold
        while more_comments:
            item = heappop(more_comments)
            if remaining is not None and remaining <= 0 or item.count < threshold:
                skipped.append(item)
                item._remove_from.remove(item)
                continue

            new_comments = item.comments(update=False)
            if remaining is not None:
                remaining -= 1

            # Add new MoreComment objects to the heap of more_comments
            for more in self._gather_more_comments(new_comments, self._comments):
                more.submission = self._submission
                heappush(more_comments, more)
            # Insert all items into the tree
            for comment in new_comments:
                self._insert_comment(comment)

            # Remove from forest
            item._remove_from.remove(item)

        return more_comments + skipped
