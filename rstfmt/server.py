import argparse
import asyncio
import functools
import logging
import time
from concurrent import futures

import docutils

from aiohttp import web

from . import rst_extras, rstfmt


class ParseError(Exception):
    pass


def do_format(width: int, s: str) -> str:
    # Unpickling SystemMessage objects is broken for some reason, so raising them directly fails;
    # replace them with our own sentinel class.
    try:
        return rstfmt.format_node(width, rstfmt.parse_string(s))
    except docutils.utils.SystemMessage as e:
        raise ParseError(str(e))


async def handle(pool: futures.Executor, req: web.Request) -> web.Response:
    width = int(req.headers.get("X-Line-Length", 72))
    body = await req.text()

    t0 = time.perf_counter()

    try:
        text = await asyncio.get_event_loop().run_in_executor(pool, do_format, width, body)
        resp = web.Response(text=text)
    except ParseError as e:
        logging.warning(f"Failed to parse input: {e}")
        resp = web.Response(status=400, reason=str(e))
    except Exception as e:
        logging.exception("Error while handling request")
        resp = web.Response(status=500, reason=str(e))

    t1 = time.perf_counter()

    dt = int(1000 * (t1 - t0))
    print(f"Finished request: {dt:3} ms, {len(body):5} chars")
    return resp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind-host", default="localhost")
    parser.add_argument("--bind-port", type=int, default=5219)
    args = parser.parse_args()

    rst_extras.register()

    with futures.ProcessPoolExecutor() as pool:
        app = web.Application()
        app.add_routes([web.post("/", functools.partial(handle, pool))])
        web.run_app(app, host=args.bind_host, port=args.bind_port)


if __name__ == "__main__":
    main()
