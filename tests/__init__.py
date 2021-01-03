"""docstrfmt Test Suite."""
import black
import docutils.nodes


def iter_descendants(node):
    for c in node.children:
        yield c
        yield from iter_descendants(c)


def text_contents(node):
    return "".join(
        n.astext() for n in iter_descendants(node) if isinstance(n, docutils.nodes.Text)
    )


def node_eq(node1, node2):
    if type(node1) is not type(node2):  # pragma: no cover
        print("different type")
        return False

    if isinstance(node1, docutils.nodes.Text):
        return bool(node1.astext().split() == node2.astext().split())
    else:
        sentinel = object()
        for k in ["name", "refname", "refuri"]:
            if node1.attributes.get(k, sentinel) != node2.attributes.get(
                k, sentinel
            ):  # pragma: no cover
                print("different attributes")
                print(node1.attributes)
                print(node2.attributes)
                return False

    if isinstance(node1, docutils.nodes.literal_block):
        if "python" in node1["classes"]:

            # Check that either the outputs are equal or both calls to Black fail to parse.
            t1 = t2 = object()
            try:
                t1 = black.format_str(text_contents(node1), mode=black.FileMode())
            except black.InvalidInput:  # pragma: no cover
                pass
            try:
                t2 = black.format_str(text_contents(node2), mode=black.FileMode())
            except black.InvalidInput:  # pragma: no cover
                pass
            return bool(t1 == t2)

    if len(node1.children) != len(node2.children):  # pragma: no cover
        print("different num children")
        for i, c in enumerate(node1.children):
            print(1, i, c)
        for i, c in enumerate(node2.children):
            print(2, i, c)
        return False
    return all(node_eq(c1, c2) for c1, c2 in zip(node1.children, node2.children))
