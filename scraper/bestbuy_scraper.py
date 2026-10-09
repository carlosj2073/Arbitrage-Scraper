import logging
import random
import re
from decimal import Decimal
from types import TracebackType
from typing import Literal, Self

from patchright.sync_api import TimeoutError as PatchrightTimeoutError
from patchright.sync_api import sync_playwright as patchright_sync_playwright
from playwright.sync_api import Browser, Page, Playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright as stock_sync_playwright
from playwright_stealth import Stealth

from scraper.logger import get_logger


class BestBuyScraper:
    website = "bestbuy"
    MAX_LAUNCH_RETRIES = 3


    def __init__(self, url: str, logger: logging.Logger, setup: Literal["stock", "patchright"] = "stock", headless: bool = False) -> None:
        self.url = url
        self.logger = logger
        self.setup = setup
        self.headless = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
 
    def __enter__(self) -> Self:
        self.launch()
        return self

    def __exit__(
        self,
        exec_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()           

    def launch(self) -> None:
        """Starts Playwright and navigates to url with retry logic on transient failures."""
        self.logger.info (f"Initiating playwright and launching {self.website}.com")

        # Determines the setup 
        if self.setup == "stock" :
            self.playwright = stock_sync_playwright().start()
            timeout_error = PlaywrightTimeoutError
        else:
            self.playwright = patchright_sync_playwright().start()  # type: ignore[assignment]  # patchright mirrors playwright's API
            timeout_error = PatchrightTimeoutError  # type: ignore[assignment]

        for attempt in range(1, self.MAX_LAUNCH_RETRIES + 1):
            try:
                self.browser = self.playwright.chromium.launch(headless=self.headless, timeout=30_000)  # type: ignore[assignment]
                self.page = self.browser.new_page()
                if self.setup == "stock":
                    Stealth().apply_stealth_sync(self.page)
                self.page.goto(self.url, timeout=30_000)
                self.logger.info(f"Launched browser and navigated to {self.url}")
                return
            except timeout_error as e:
                self.logger.warning(f"Launch attempt {attempt} failed: {e}")
                if self.browser:
                    self.browser.close()
                if attempt == self.MAX_LAUNCH_RETRIES:
                    raise

    def scroll(self) -> None:
        """Scrolls down the page to product cards to combat lazy loading selectors."""
        assert self.page is not None
        previous_height = 0

        for i in range(10): # range hard cap avoids inifinite scroll
            scroll_amount = random.randint(300, 800)
            self.page.mouse.wheel(0, scroll_amount)
            self.page.wait_for_timeout(random.randint(1000, 3000))
            current_height = self.page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break # stops scrolling at the bottom of the page
            previous_height = current_height

        self.logger.info(f"Scroll finished after {i+1} iterations. Final height: {current_height}")
        
    def scrape(self) -> list[dict]:
        """Scrapes product data from page per DOM product card at a time. """
        assert self.page is not None
        results = []
        seen_pids = set() # used for deduplication step

        self.page.wait_for_selector('[data-product-id]')
        self.scroll()

        cards = self.page.locator('[data-product-id]').all()
        self.logger.info(f"Found {len(cards)} product cards")
        
        for card in cards:
            try:
                website_pid = card.get_attribute('data-product-id')
                if website_pid in seen_pids:
                    self.logger.warning(f"Skipping repeated card: website_pid = {website_pid}")
                    continue
                listing = card.locator('.product-title').inner_text()
                price_raw = card.locator('[data-testid="price-block-customer-price"]').nth(0).inner_text() 
                url = card.locator('.product-list-item-link').get_attribute('href')
                image = card.locator(' [data-testid="product-image"]').get_attribute('src')

                seen_pids.add(website_pid)
                results.append({
                    "listing" : listing,
                    "price_usd" : self.parse_price(price_raw),
                    "website_pid" : website_pid,
                    "url" : url,
                    "image" : image,
                    "brand" : None

                })

            except Exception:
                self.logger.exception("Skipping card due to error")
        return results

    
    @staticmethod
    def parse_price(price_raw: str) -> Decimal:
        "formats and converts a price string to Decimal"
        match = re.search(r'\$([\d,]+\.\d{2})', price_raw)
        if not match:
            raise ValueError(f"No price found in: {price_raw}")
        price_str = match.group(1).replace(',','')
        return Decimal(price_str)

if __name__ == "__main__":
    url = "https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&st=headphones"
    logger = get_logger("bestbuy")

    with BestBuyScraper(url=url, logger=logger) as scraper:
        results = scraper.scrape()

    for result in results:
        print(result)
    
    