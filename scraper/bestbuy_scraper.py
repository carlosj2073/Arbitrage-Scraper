import logging
from logger import get_logger
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from decimal import Decimal
import re

class BestBuyScraper:
    website = "bestbuy"

    def __init__(self, url: str, logger: logging.Logger) -> None:
        self.url = url
        self.logger = logger
        self.playwright = None
        self.browser = None
        self.page = None
    
    def launch(self) -> None: 
        self.logger.info (f"Initiating playwright and launching {self.website}.com")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        Stealth().apply_stealth_sync(self.page)
        self.page.goto(self.url)
        
        self.logger.info(f"Launched browser and navigated to {self.url}")

    def scrape(self) -> list[dict]:
        results = []
        seen_pids = set() # used for deduplication step

        self.page.wait_for_selector('[data-product-id]')

        cards = self.page.locator('[data-product-id]').all()
        self.logger.info(f"Found {len(cards)} product cards")
        
        for card in cards:
            try:
                listing = card.locator('.product-title').inner_text()
                price_raw = card.locator('[data-testid="price-block-customer-price"]').nth(0).inner_text() 
                website_pid = card.get_attribute('data-product-id')
                url = card.locator('.product-list-item-link').get_attribute('href')
                image = card.locator(' [data-testid="product-image"]').get_attribute('src')

                if website_pid not in seen_pids:
                    seen_pids.add(website_pid)
                    results.append({
                        "listing" : listing,
                        "price_usd" : BestBuyScraper.parse_price(price_raw),
                        "website_pid" : website_pid,
                        "url" : url,
                        "image" : image,
                        "brand" : None

                    })
                else:
                    self.logger(f"skipping repeated card: listing={listing}, website_pid={website_pid}")
                    continue

            except Exception as e:
                self.logger.warning(f"Skipping card due to error: {e}")
        return results
    
    @staticmethod
    def parse_price(price_raw: str) -> Decimal:
        match = re.search(r'\$([\d,]+\.\d{2})', price_raw)
        if not match:
            raise ValueError(f"No price found in: {price_raw}")
        price_str = match.group(1).replace(',','')
        return Decimal(price_str)

if __name__ == "__main__":
    url = "https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&st=headphones"
    logger = get_logger("bestbuy")

    scraper = BestBuyScraper(url=url, logger=logger)
    scraper.launch()
    results = scraper.scrape()

    for result in results:
        print(result("listing", "price_usd", "website_pid", "url" , "brand"), "\n")
                 