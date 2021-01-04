"""Prepare py.test."""
import os
import shutil

import black
import pytest
from aiohttp import web
from click.testing import CliRunner

from docstrfmt import Manager
from docstrfmt.server import handler
from tests import node_eq


def run_test(manager, file, width, test_string):
    doc = manager.parse_string(file, test_string)
    output = manager.format_node(width, doc)
    doc2 = manager.parse_string(file, output)
    output2 = manager.format_node(width, doc2)
    assert node_eq(doc, doc2)
    assert output == output2


@pytest.fixture
def client(loop, aiohttp_client):
    app = web.Application()
    app.router.add_post("/", handler)
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def manager():
    manager = Manager(None, black.Mode())
    yield manager


@pytest.fixture
def runner():
    runner = CliRunner()
    files_to_copy = os.path.abspath("tests/test_files")
    with runner.isolated_filesystem() as temp_dir:
        shutil.copytree(files_to_copy, f"{temp_dir}/tests/test_files")
        yield runner
