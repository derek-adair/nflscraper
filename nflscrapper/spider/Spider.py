import asyncio
from contextlib import closing
import time

import aiohttp

NFL_DOT_COM = 'https://www.nfl.com'

class Spider(object):
    async def fetch_page(session, url, request_increment=2):
        """Get one page.
        """
        request_url = '{}:{}/{}'.format(domain, 80, request_increment)
        with aiohttp.Timeout(10):
            async with session.get(request_url) as response:
                assert response.status == 200
                return await response.text()

    async def fetch_multiple_pages(urls, domain=NFL_DOT_COM, request_increment=2):
        """Fetch multiple pages.
        """
        tasks = []
        pages = []
        start = time.perf_counter()

        async with closing(asyncio.get_event_loop()) as loop:
            async with aiohttp.ClientSession(loop=loop) as session:
                tasks.append(fetch_page(session, domain, request_increment, url))
                pages = await loop.run_until_complete(asyncio.gather(*tasks))
        duration = time.perf_counter() - start
        msg = 'It took {:4.2f} seconds  to request {}'
        print(msg.format(duration, url))
        return pages
