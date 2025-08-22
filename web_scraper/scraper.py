import asyncio
import random
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

from .config import HEADLESS_MODE, RETRY_COUNT, RETRY_DELAY_SECONDS, SELECTORS, USER_AGENTS
from .data_parser import DataParser

log = logging.getLogger(__name__)


class WebScraper:
    """An enhanced web scraper with stealth capabilities to handle anti-bot measures."""

    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self.parser = DataParser()

    async def _initialize(self):
        """Initializes Playwright resources."""
        if not self._initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=HEADLESS_MODE)
            page = await self.browser.new_page(user_agent=random.choice(USER_AGENTS))
            await Stealth().apply_stealth_async(page)
            self.page = page
            self._initialized = True

    async def _execute_with_retries(self, action, action_name=""):
        """Wrapper to execute a Playwright action with retry logic."""
        await self._initialize()
        for attempt in range(RETRY_COUNT):
            try:
                return await action()
            except PlaywrightTimeoutError:
                log.debug(f"Attempt {attempt + 1} failed for '{action_name}'. Retrying...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            except Exception as e:
                log.error(f"An unexpected error occurred during '{action_name}': {e}")
                break
        log.info(f"Action '{action_name}' failed after {RETRY_COUNT} attempts.")
        return None

    async def navigate_to_page(self):
        """Navigates to the product page with retry logic."""
        async def navigate():
            log.info("Navigating to page... This may take a moment due to Cloudflare checks.")
            await self.page.goto(self.url, wait_until='domcontentloaded', timeout=90000)
            await self.page.wait_for_selector(SELECTORS['product']['title'], state='visible', timeout=45000)
            log.debug('Selector wait finished')
            return True

        if await self._execute_with_retries(navigate, "Navigate to page"):
            log.info("Successfully navigated to page and bypassed Cloudflare.")
            return True
        return False

    async def get_product_info(self):
        """Orchestrates the extraction of product information."""
        await self._initialize()
        return await self.parser.extract_product_info(self.page)

    async def get_reviews(self):
        """Extracts all reviews, handling pagination and dynamic content."""
        await self._initialize()
        reviews_list = []
        try:
            log.info("Navigating to reviews tab...")
            await self._execute_with_retries(
                lambda: self.page.locator(SELECTORS['product']['reviews_link']).click(),
                "Click Reviews Tab"
            )
            await self.page.wait_for_selector(SELECTORS['reviews']['container'], timeout=90000)

            current_page = 1
            while True:
                log.debug(f"Scraping reviews from page {current_page}...")
                await asyncio.sleep(random.uniform(1, 2))
                review_items = await self.page.locator(SELECTORS['reviews']['review_item']).all()
                if not review_items:
                    log.info(f"No reviews found on page {current_page}. Ending scrape.")
                    break

                parse_tasks = [self.parser.parse_review(item) for item in review_items]
                parsed_reviews_on_page = await asyncio.gather(*parse_tasks)
                reviews_list.extend([review for review in parsed_reviews_on_page if review])

                next_page_num = current_page + 1
                next_page_locator = self.page.locator(f'ol.paginations a.button:text-is("{next_page_num}")')

                if await next_page_locator.is_visible():
                    print(f"Navigating to page {next_page_num}...")
                    # had to add this random click to get rid of overlays
                    await self.page.locator('body').click(position={'x': 5, 'y': 5})

                    await next_page_locator.click()

                    current_page = next_page_num
                    
                else:
                    log.info("Last page of reviews reached.")
                    break

        except Exception as e:
            log.error(f"A critical error occurred while extracting reviews: {e}")
        return reviews_list

    async def close(self):
        """Closes the browser and Playwright instance."""
        log.info("Closing browser.")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()