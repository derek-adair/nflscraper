import re
import sys
import logging
import time
import random
import asyncio
import asyncio

import aiofiles
import aiohttp
from aiohttp import ClientSession
from asyncio_throttle import Throttler

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("nfl-scrape-async")
logging.getLogger("chardet.charsetprober").disabled = True

URL_STR = "https://www.httpbin.org?year={}&&week={}{}"

SEASON_PHASES = (
            ('PRE', range(0, 4)),
            ('REG', range(1, 17)),
            ('POST', range(1, 4)),
        )

def build_urls(year):
    urls = []
    for phase_dict in SEASON_PHASES:
        for week_num in phase_dict[1]:
            urls.append(URL_STR.format(year, phase_dict[0], week_num))

    return urls

async def fetch_html(url: str, session: ClientSession, **kwargs) -> str:
    """GET request wrapper to fetch page HTML.

    kwargs are passed to `session.request()`.
    """
    resp = await session.request(method="GET", url=url, **kwargs)
    resp.raise_for_status()
    logger.info("Got response [%s] for URL: %s", resp.status, url)
    html = await resp.text()
    return html

async def worker(throttler, session, urls):
    for url in urls:
        async with throttler:
            print(time.time(), 'Worker: Bang!')
            await fetch_html(url, session)

async def main():
    throttler = Throttler(rate_limit=3, period=2)
    async with ClientSession() as session:
        urls = build_urls(2020)
        tasks = [loop.create_task(worker(throttler, session, urls))]
        await asyncio.wait(tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
