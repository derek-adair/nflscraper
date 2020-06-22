#!/usr/bin/env python3
# areq.py

"""Asynchronously get links embedded in multiple pages' HMTL."""
import json
import sys
import logging
import time
import asyncio
import os

from bs4 import BeautifulSoup

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

URL_STR = "https://www.nfl.com/schedules/{year}/{phase}{week_num}"

SEASON_PHASES = (
            #('PRE', range(0, 4)),
            ('REG', range(1,17+1)),
            ('POST', range(1, 4+1)),
        )

def build_urls(year):
    urls = []
    for phase_dict in SEASON_PHASES:
        season_phase, week_range = phase_dict
        for week_num in week_range:
            urls.append(URL_STR.format(year=year, phase=season_phase, week_num=week_num))
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
    games = []
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
        page_soup = BeautifulSoup(html, 'html.parser')

        matchup_groups = page_soup.select("section.nfl-o-matchup-group")

        for group in matchup_groups:
            datestr = group.find("h2", class_="d3-o-section-title").get_text()

            game_strips = group.select("div.nfl-c-matchup-strip")
            for strip in game_strips:
                team_abbv = strip.select("span.nfl-c-matchup-strip__team-abbreviation")
                games += [{
                            "date": datestr,
                            "time": strip.select("span.nfl-c-matchup-strip__date-time")[0].get_text().strip(),
                            "away": team_abbv[0].get_text().strip(),
                            "home": team_abbv[1].get_text().strip(),
                        }]

        logger.info("Found %d links for %s", len(games), url)
        return games

async def write_results(data: dict) -> None:
    outfile = os.path.join(os.path.dirname(__file__), 'schedule.json')
    json_str = json.dumps(data)
    async with aiofiles.open(outfile, "w+") as f:
        await f.write(json_str)
        logger.info("Wrote results for source URLs")


async def main():
    """Main program for setting up task and throttler
    """
    throttler = Throttler(rate_limit=3, period=3)
    async with ClientSession() as session:
        urls = build_urls(2020)
        tasks = [loop.create_task(worker(throttler, session, urls))]
        await asyncio.wait(tasks)

async def worker(throttler, session, urls):
    """Worker that will take a list of urls and parse/throttle them
    """
    data = list()
    logger.info("Worker fetching {} urls".format(len(urls)))
    for url in urls:
        async with throttler:
            data += await parse(url, session)
    await write_results(data)

if __name__ == "__main__":
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."

    #parser = argparse.ArgumentParser(
    #    description='Updates nflgame\'s schedule',
    #    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    #aa = parser.add_argument
    #aa('--year', default=datetime.now().year, type=int,
    #   help='Force the update to a specific year.')

    #args = parser.parse_args()

    #urls = build_urls(args.year)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
