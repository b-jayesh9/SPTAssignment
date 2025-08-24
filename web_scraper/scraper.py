import asyncio
import random
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

from .config import HEADLESS_MODE, RETRY_COUNT, RETRY_DELAY_SECONDS, SELECTORS, USER_AGENTS
from .data_parser import DataParser

log = logging.getLogger(__name__)


class WebScraper:
    """
    A web scraping class designed to extract product information and reviews from NewEgg.

    This class uses Playwright for browser automation and implements stealth techniques
    to bypass anti-bot measures. It handles page navigation, data extraction,
    and pagination with built-in retry mechanisms for reliability.

    Key features:
    - Asynchronous operation for improved performance
    - Anti-detection measures using playwright-stealth
    - Automatic retry mechanism for failed requests
    - Random user agent rotation
    - Cloudflare bypass capability
    - Structured data extraction for products and reviews

    Main methods:
    - navigate_to_page(): Navigates to target URL and handles Cloudflare checks
    - get_product_info(): Extracts product details from the page
    - get_reviews(): Scrapes all reviews including pagination handling
    """

    def __init__(self, url):
        """Constructor for our scraper. Setting up all the basic things here."""
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None
        self.logger = logging.getLogger(__name__)
        # To make sure we only start playwright once.
        self._initialized = False
        self.parser = DataParser()

    async def _initialize(self):
        """
        Start up Playwright and spin up a browser.
        """
        if not self._initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=HEADLESS_MODE)
            # We need to act like a real user, so a random user agent is picked.
            page = await self.browser.new_page(user_agent=random.choice(USER_AGENTS))
            # Use playwright stealth to make it more robust against known blockers.
            await Stealth().apply_stealth_async(page)
            self.page = page
            self._initialized = True

    async def _execute_with_retries(self, action, action_name=""):
        """
        Sometimes the connection is not good or the page is slow.
        This method will try the same thing a few times before giving up. Very useful for making our scraper strong.
        """
        await self._initialize()
        for attempt in range(RETRY_COUNT):
            try:
                return await action()
            except PlaywrightTimeoutError:
                # A timeout happened. Maybe network/page issues. Wait and try again.
                log.debug(f"Attempt {attempt + 1} failed for '{action_name}'. Retrying...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            except Exception as e:
                # Some other unexpected issue. Stop after the retry count is exceeded.
                log.error(f"An unexpected error occurred during '{action_name}': {e}")
                break
        log.info(f"Action '{action_name}' failed after {RETRY_COUNT} attempts.")
        return None

    async def navigate_to_page(self):
        """Navigates to the product page with retry logic to bypass cloudflare checks."""
        async def navigate():
            log.info("Navigating to page... This may take a moment due to Cloudflare checks.")
            # We tell it to wait until the page structure is ready.
            await self.page.goto(self.url, wait_until='domcontentloaded', timeout=90000)
            # Just to be sure, we wait for the product title to actually appear on the screen.
            await self.page.wait_for_selector(SELECTORS['product']['title'], state='visible', timeout=45000)
            log.debug('Selector wait finished')
            return True

        # We use our retry wrapper to make sure the navigation is successful.
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
            # First, we find and click the 'Reviews' link to show them.
            await self._execute_with_retries(
                lambda: self.page.locator(SELECTORS['product']['reviews_link']).click(),
                "Click Reviews Tab"
            )
            # Wait for the review container to load up.
            await self.page.wait_for_selector(SELECTORS['reviews']['container'], timeout=90000)

            current_page = 1
            # We will keep going page by page until there are no more pages left.
            while True:
                log.debug(f"Scraping reviews from page {current_page}...")
                await asyncio.sleep(random.uniform(1, 2)) # A small, random pause.
                # On each page, we find all the individual review items.
                review_items = await self.page.locator(SELECTORS['reviews']['review_item']).all()
                if not review_items:
                    # If no reviews are there, we are done, so we can stop.
                    log.info(f"No reviews found on page {current_page}. Ending scrape.")
                    break

                # We will use asyncio to parse all the reviews on the page at the same time.
                parse_tasks = [self.parser.parse_review(item) for item in review_items]
                parsed_reviews_on_page = await asyncio.gather(*parse_tasks)
                # After parsing, we add non-empty reviews to our main list.
                reviews_list.extend([review for review in parsed_reviews_on_page if review])

                # Now, we look for the next page button.
                next_page_num = current_page + 1
                next_page_locator = self.page.locator(f'ol.paginations a.button:text-is("{next_page_num}")')

                if await next_page_locator.is_visible():
                    print(f"Navigating to page {next_page_num}...")
                    # Trick to remove random overlays.
                    await self.page.locator('body').click(position={'x': 5, 'y': 5})

                    # Click the next page button to load more reviews.
                    await next_page_locator.click()

                    # And we update our page number count.
                    current_page = next_page_num
                    
                else:
                    # If no next page button, it means we are at the last page.
                    log.info("Last page of reviews reached.")
                    break

        except Exception as e:
            log.error(f"A critical error occurred while extracting reviews: {e}")
        return reviews_list

    async def close(self):
        """This will shut down the browser and Playwright after execution"""
        log.info("Closing browser.")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()