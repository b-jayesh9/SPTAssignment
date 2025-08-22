import logging
import re
import time
import random
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

# **** Configuration Section ****

BASE_URL = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
HEADLESS_MODE = False
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 5

SELECTORS = {
    "product": {
        "title": 'h1.product-title', "brand_image": '.product-brand-logo img',
        "current_price": 'li.price-current',
        "reviews_link": 'a[data-nav-title="Reviews"]',
        "rating_text": 'div.product-rating .rating-views-text',
        "description_list": 'div.product-bullets ul li'
    },
    "reviews": {
        "container": 'div.comments',
        "review_item": 'div.comments-cell',
        "author": 'div.comments-name',
        # fetch rating from class
        "rating_icon": 'i[class^="rating rating-"]',
        "title": 'span.comments-title-content',
        "comment_body": 'div.comments-content',
        # check title
        "date": 'div.comments-title > span.comments-text',
        "verified_badge": 'div.comments-verified-owner',
        "next_page_button": 'a.paginations-next'
    },
    # find any dialog popup and fetch its close button
    "dialogs": {"close_promo_button": '[aria-label="close"]'}
}
# *** End Configuration Section ***


class ResilientNeweggScraper:
    """An enhanced web scraper with stealth capabilities to handle anti-bot measures."""
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0'
    ]

    def __init__(self, url):
        self.url = url
        self.playwright = None
        self.browser = None
        self.page = None
        self.selectors = SELECTORS
        self.logger = logging.getLogger()
        self._initialized = False

    async def _initialize(self):
        """Initialize playwright resources"""
        if not self._initialized:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=HEADLESS_MODE)

            # Create a new page and apply the stealth patches to it to run it in stealth mode
            page = await self.browser.new_page(user_agent=random.choice(self.USER_AGENTS))
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
                print(f"Attempt {attempt + 1} failed for '{action_name}'. Retrying...")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            except Exception as e:
                print(f"An unexpected error occurred during '{action_name}': {e}")
                break
        print(f"Action '{action_name}' failed after {RETRY_COUNT} attempts.")
        return None

    async def navigate_to_page(self):
        """Navigates to the product page with retry logic."""

        async def navigate():
            print("Navigating to page... This may take a moment due to Cloudflare checks.")
            await self.page.goto(self.url, wait_until='domcontentloaded', timeout=90000)
            print('dom loaded')
            # A longer wait here for the main product title to ensure Cloudflare has finished
            await self.page.wait_for_selector(self.selectors['product']['title'], state='visible', timeout=45000)
            print('selector wait')
            return True

        if await self._execute_with_retries(navigate, "Navigate to page"):
            print("Successfully navigated to page and bypassed Cloudflare.")
            return True
        return False

    async def extract_product_info(self):
        """Extracts product information using configured selectors."""
        await self._initialize()

        print("Extracting product information...")
        info = {}
        try:
            info['title'] = await self.page.locator(self.selectors['product']['title']).inner_text()
            info['brand'] = await self.page.locator(self.selectors['product']['brand_image']).get_attribute('title')
            info['price'] = await self.page.locator(self.selectors['product']['current_price']).inner_text()
            info['ratings'] = await self.page.locator(self.selectors['product']['rating_text']).first.inner_text()
            reviews_text = info['ratings'].split(' ')[0].replace('(', '').replace(')', '')
            info['reviews_count'] = int(reviews_text) if reviews_text.isdigit() else 0
            info['description'] = "\n".join(
                await self.page.locator(self.selectors['product']['description_list']).all_inner_texts())
            print(info)
            return info
        except Exception as e:
            print(f"Could not extract all product information. Some fields may be missing. Error: {e}")
            return info

    async def _parse_review(self, item):
        try:
            rating = 0
            rating_class = await item.locator(self.selectors['reviews']['rating_icon']).get_attribute(
                'class')
            if rating_class:
                match = re.search(r'rating-(\d+)', rating_class)
                if match:
                    rating = int(match.group(1))

            review_data = {
                'reviewer_name': await item.locator(self.selectors['reviews']['author']).inner_text(),
                'rating': rating,
                'review_title': await item.locator(self.selectors['reviews']['title']).inner_text(),
                'review_body': await item.locator(self.selectors['reviews']['comment_body']).inner_text(),
                'date_of_review': await item.locator(self.selectors['reviews']['date']).inner_text(),
                'verified_buyer': 'Yes' if await item.locator(
                    self.selectors['reviews']['verified_badge']).is_visible() else 'No'
            }
        except Exception as e:
            print(f"Skipping a review due to an extraction error: {e}")
            review_data = None

        return review_data

    async def extract_reviews(self):
        """Extracts reviews with advanced handling for pagination and dynamic content."""
        await self._initialize()

        reviews_list = []
        try:
            print("Navigating to reviews tab...")
            await self._execute_with_retries(
                lambda: self.page.locator(self.selectors['product']['reviews_link']).click(),
                "Click Reviews Tab"
            )
            await self.page.wait_for_selector(self.selectors['reviews']['container'], timeout=90000)
            current_page = 1
            while True:
                print(f"Scraping reviews from page {current_page}...")
                await asyncio.sleep(random.uniform(1, 2))
                review_items = await self.page.locator(self.selectors['reviews']['review_item']).all()
                if not review_items:
                    print(f"No reviews found on page {current_page}. Ending scrape.")
                    break

                # --- START OF FOR LOOP ---
                # This loop now ONLY processes reviews on the current page.
                parse_tasks = [self._parse_review(item) for item in review_items]
                parsed_reviews_on_page = await asyncio.gather(*parse_tasks)
                # Filter out any None results from failed parses and add to the main list
                reviews_list.extend([review for review in parsed_reviews_on_page if review])

                # --- END OF FOR LOOP ---

                # --- PAGINATION LOGIC (MOVED HERE) ---
                # This logic now runs only ONCE per page, after all reviews are scraped.
                next_page_num = current_page + 1
                next_page_locator = self.page.locator(f'ol.paginations a.button:text-is("{next_page_num}")')

                if await next_page_locator.is_visible():
                    print(f"Navigating to page {next_page_num}...")
                    # had to add this random click to get rid of overlays
                    await self.page.locator('body').click(position={'x': 5, 'y': 5})

                    await next_page_locator.click()

                    current_page = next_page_num
                else:
                    print("Last page of reviews reached.")
                    break

        except Exception as e:
            print(f"A critical error occurred while extracting reviews: {e}")
        return reviews_list

    async def close(self):
        """Closes the browser and Playwright instance."""
        print("Closing browser.")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# Example usage functions
async def main_async():
    """Example async usage"""
    scraper = ResilientNeweggScraper(BASE_URL)

    try:
        if await scraper.navigate_to_page():
            print('inside')
            # Scrape product data
            product_info = await scraper.extract_product_info()
            print(product_info)

            if product_info and product_info.get('title'):
                print(f"Product '{product_info['title']}' data extracted")

                # Scrape review data
                reviews = await scraper.extract_reviews()
                if reviews:
                    print(f"Successfully extracted {len(reviews)} reviews.")
                else:
                    print("No reviews were extracted.")
            else:
                print("Failed to extract essential product information. Aborting.")

    except Exception as e:
        print(f"A fatal error occurred in the main process: {e}")

    finally:
        await scraper.close()
        print("--- Async Scraper finished ---")


if __name__ == '__main__':
    asyncio.run(main_async())
