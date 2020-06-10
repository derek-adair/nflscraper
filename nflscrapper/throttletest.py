import re
import json
import sys
import logging
import time
import random
import asyncio
import os

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

async def parse(url: str, session: ClientSession, **kwargs) -> set:
    games = [
   {
    "away": "BUF",
    "day": 9,
    "eid": "2009080950",
    "gamekey": "54723",
    "home": "TEN",
    "month": 8,
    "season_type": "PRE",
    "time": "8:00",
    "wday": "Sun",
    "week": 0,
    "year": 2009
   }
   ]
    try:
        html = await fetch_html(url=url, session=session, **kwargs)
    except (
        aiohttp.ClientError,
        aiohttp.http_exceptions.HttpProcessingError,
    ) as e:
        logger.error(
            "aiohttp exception for %s [%s]: %s",
            url,
            getattr(e, "status", None),
            getattr(e, "message", None),
        )
        return games
    except Exception as e:
        logger.exception(
            "Non-aiohttp exception occured:  %s", getattr(e, "__dict__", {})
        )
        return games
    else:
        logger.info("Found %d links for %s", len(games), url)
        return games

async def write_results(data: dict) -> None:
    outfile = os.path.join(os.path.dirname(__file__), 'schedule.json')
    json_str = json.dumps(data)
    async with aiofiles.open(outfile, "w+") as f:
        await f.write(json_str)
        logger.info("Wrote results for source URLs")

async def worker(throttler, session, urls):
    games = list()
    logger.info("Worker fetching {} urls".format(len(urls)))
    for url in urls:
        async with throttler:
            games += await parse(url, session)
    await write_results(games)

async def main():
    throttler = Throttler(rate_limit=3, period=.1)
    async with ClientSession() as session:
        urls = build_urls(2020)
        tasks = [loop.create_task(worker(throttler, session, urls))]
        await asyncio.wait(tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
