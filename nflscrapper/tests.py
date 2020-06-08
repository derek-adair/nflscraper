import unittest

from . import ScheduleSpider

class TestScheduleSpider(unittest.TestCase):
    def test_build_urls(self):
        year = 2020

        urls = ScheduleSpider.build_urls(year)

        assert len(urls) == 23
        assert urls[0] == "https://www.nfl.com/schedules/2020/PRE0"
