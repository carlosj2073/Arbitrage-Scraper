import logging
from logger import get_logger
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from decimal import Decimal
import re

class GoogleScraper:
    website = "google"
    def __init__(self, url : str, logger : logging.Logger) -> None:
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
        seen_pids = set() # used for deduplication step


        self.page.wait_for_selector('div.liKJmf.wTrwWd[data-pid]')
        cards = self.page.locator('div.liKJmf.wTrwWd[data-pid]').all()
        self.logger.info(f"Found {len(cards)} product cards")

        for card in cards:
            try:
                listing = card.locator('.gkQHve.SsM98d.RmEs5b').first.inner_text()
                price_raw = card.locator('[aria-label*="Current Price"]').first.inner_text()
                website_pid = card.get_attribute('data-pid')

                # finds correct image excluding base64 and non-product image attributes
                image = None
                try:
                    i_locators = card.locator('img.VeBrne').all()

                    for i_locator in i_locators:
                        i_attribute = i_locator.get_attribute('src', timeout=5000)

                        if i_attribute.startswith('data:'):
                            image = None
                            continue
                        else:
                            image = i_attribute
                            break

                except Exception as e:
                    self.logger.warning(f"Skipping image due to: {e}")
                
                # deduplicates seen_pid products
                if website_pid not in seen_pids:
                    seen_pids.add(website_pid)   
                    results.append({
                        "listing" : listing,
                        "price_usd" : GoogleScraper.parse_price(price_raw),
                        "website_pid" : website_pid,    
                        "image" : image,
                        "brand" : None
                    })
                else:
                    self.logger.info(f"skipping repeated card: listing={listing}, website_pid={website_pid}")
                    continue

            except Exception as e:
                self.logger.warning(f"Skipping card due to error: {e}")
            
        return results
    
    # filters, parses, and changes types for true price in price_raw
    @staticmethod
    def parse_price(price_raw: str) -> Decimal:
        match = re.search(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_raw)
        if not match:
            raise ValueError(f"No price found in: {price_raw}")
        price_str = match.group(1).replace(',', '')
        return Decimal(price_str)
    
if __name__ == "__main__":
    logger = get_logger("google")
    url = "https://www.google.com/search?q=headphones&udm=28&shopmd=1"

    scraper = GoogleScraper(url=url, logger=logger)
    scraper.launch()
    results = scraper.scrape()

    for result in results:
        print(result)










