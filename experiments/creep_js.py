from scraper.bestbuy_scraper import BestBuyScraper
from scraper.logger import get_logger

with BestBuyScraper(url="https://abrahamjuliot.github.io/creepjs/", logger=get_logger("creep_js"), setup="patchright") as scraper:
    assert scraper.page is not None
    scraper.page.wait_for_timeout(10_000)
    scraper.page.screenshot(path="experiments/output/creepjs_patchright.png",full_page = True)