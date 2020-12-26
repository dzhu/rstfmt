"""Prepare py.test."""
import black
import pytest
from aiohttp import web

from docstrfmt import Manager
from docstrfmt.server import handler
from tests import node_eq


def run_test(manager, file, width, test_string):
    doc = manager.parse_string(test_string)
    output = manager.format_node(file, width, doc)
    doc2 = manager.parse_string(output)
    output2 = manager.format_node(file, width, doc2)
    assert node_eq(doc, doc2)
    assert output == output2


@pytest.fixture
def client(loop, aiohttp_client):
    app = web.Application()
    app.router.add_post("/", handler)
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture()
def manager():
    manager = Manager(None, black.Mode())
    yield manager
