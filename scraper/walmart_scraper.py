from logger import get_logger
import logging
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from decimal import Decimal


class WalmartScraper:

    website = "walmart"

    def __init__(self, url: str, logger: logging.Logger) -> None:
        self.url = url
        self.logger = logger  
        self.playwright = None
        self.browser = None
        self.page = None
       

    def launch(self) -> None:

        self.logger.info(f"Initiating playwright and launching {self.website}.com")

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        Stealth().apply_stealth_sync(self.page)
        self.page.goto(self.url)

        self.logger.info(f"Launched browser and navigated to {self.url}")
    
    def scrape(self) -> list[dict]:
        results = []
        
        # Determines # of products per page
        self.page.wait_for_selector('[data-testid="item-stack"]')
        cards = self.page.locator('[data-test-id="gpt-main"]').all()
        self.logger.info(f"Found {len(cards)} product cards")

        for card in cards:
            try: 
                listing = card.locator('[data-automation-id="product-title"]').inner_text()
                price_raw = card.locator('[data-test-id="gpt-main-price-display"]').inner_text()
                href = card.locator('a').first.get_attribute('href')
                url = href if href.startswith("http") else f"https://www.walmart.com{href}" # catches sponsered cards syntax difference
                image = card.locator('[data-testid="productTileImage"]').get_attribute('src')

                results.append({
                    "listing" : listing,
                    "price_usd" : WalmartScraper.parse_price(price_raw),
                    "url" : url,
                    "image" : image,
                    "brand" : None  
                })
            
            except Exception as e:
                self.logger.warning(f"Skipping card due to error: {e}")
        
        return results
    
    @staticmethod
    def parse_price(price_raw : str) -> Decimal:
        digits = ''.join(filter(str.isdigit, price_raw))
        return Decimal(digits) / Decimal(100)

     
if __name__ == "__main__":
    logger = get_logger("walmart")
    url = "https://www.walmart.com/search?q=headphones"

    scraper = WalmartScraper(url=url, logger=logger)
    scraper.launch()
    results = scraper.scrape()
    
    for result in results:
        print(result)