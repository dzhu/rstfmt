from unittest import mock

import pytest
from aiohttp import web
from click.testing import CliRunner

from docstrfmt import rst_extras
from docstrfmt.server import main

test_lengths = [8, 13, 34, 55, 89, 144, 72, None]


@pytest.mark.parametrize("bind_host", ["localhost", "127.0.0.1", None])
@pytest.mark.parametrize("bind_port", [80, 5219, 5555, None])
def test_click(bind_host, bind_port):
    rst_extras.register()
    web.run_app = mock.MagicMock("run_app")
    runner = CliRunner()
    args = []
    if bind_host:
        args += ["--bind-host", bind_host]
    if bind_port:
        args += ["--bind-port", bind_port]
    result = runner.invoke(main, args=args)
    assert result.exit_code == 0
    assert web.run_app.called
    if bind_host:
        assert web.run_app.call_args[1]["host"] == bind_host
    else:
        assert web.run_app.call_args[1]["host"] == "localhost"
    if bind_port:
        assert web.run_app.call_args[1]["port"] == bind_port
    else:
        assert web.run_app.call_args[1]["port"] == 5219


@pytest.mark.parametrize("length", test_lengths)
async def test_server(client, length, loop):
    rst_extras.register()
    # fill route table
    headers = {
        "X-Line-Length": f"{length}",
    }
    with open("tests/test_files/test_file.rst", "rb") as f:
        data = f.read()
    response = await client.post("/", data=data, headers=headers)
    output = await response.text()
    response = await client.post("/", data=output.encode(), headers=headers)
    output2 = await response.text()
    assert output == output2
