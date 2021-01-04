import logging
import time

import click
import docutils
from aiohttp import web

from . import Manager, rst_extras


class ParseError(Exception):  # pragma: no cover
    pass


rst_extras.register()


async def handler(request) -> web.Response:
    width = int(request.headers.get("X-Line-Length", 88))
    body = await request.text()

    start_time = time.perf_counter()
    manager = Manager(logging, None)
    try:
        try:
            text = manager.format_node(
                width, manager.parse_string("<server_input>", body)
            )
            resp = web.Response(text=text)
        except docutils.utils.SystemMessage as error:  # pragma: no cover
            raise ParseError(str(error))
    except ParseError as error:  # pragma: no cover
        logging.warning(f"Failed to parse input: {error}")
        resp = web.Response(status=400, reason=str(error))
    except Exception as error:  # pragma: no cover
        logging.exception("Error while handling request")
        resp = web.Response(status=500, reason=str(error))

    end_time = time.perf_counter()

    time_elapsed = int(1000 * (end_time - start_time))
    print(f"Finished request: {time_elapsed:3} ms, {len(body):5} chars")
    return resp


@click.command()
@click.option(
    "-h",
    "--bind-host",
    "bind_host",
    type=str,
    default="localhost",
    show_default=True,
)
@click.option(
    "-p",
    "--bind-port",
    "bind_port",
    type=int,
    default=5219,
    show_default=True,
)
def main(bind_host, bind_port) -> None:
    app = web.Application()
    app.add_routes([web.post("/", handler)])
    web.run_app(app, host=bind_host, port=bind_port)
