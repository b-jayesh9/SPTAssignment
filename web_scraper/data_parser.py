import datetime
import time
import re
import logging
from .config import SELECTORS


log = logging.getLogger(__name__)


class DataParser:
    """Handles parsing of HTML content to extract product and review data."""

    @staticmethod
    async def extract_product_info(page):
        """
        Extracts product information using the UPDATED selectors and logic.
        """
        log.info("Extracting product information from page...")
        info = {}
        try:
            info['title'] = await page.locator(SELECTORS['product']['title']).inner_text()

            # Use the new selector for brand
            info['brand'] = await page.locator(SELECTORS['product']['brand']).inner_text()

            # 1. Find the container for the selected product option.
            price_container_locator = page.locator(SELECTORS['product']['price_container'])

            # 2. Within that container, find the <strong> tag that contains a '$'.
            #    This uniquely identifies the price and resolves the ambiguity.
            price_locator = price_container_locator.locator('strong', has_text='$')
            info['price'] = await price_locator.inner_text()

            # Get the overall rating text (e.g., "4.7 out of 5 eggs") from the title attribute
            rating_element = page.locator(SELECTORS['product']['rating_element'])
            info['ratings'] = await rating_element.get_attribute('title') or "No rating text"

            # Get the review count text (e.g., "(302)") and parse the number
            reviews_count_text = await page.locator(SELECTORS['product']['reviews_count_text']).first.inner_text()
            # Clean the text by removing parentheses and other non-digit characters
            reviews_count_digits = re.search(r'\d+', reviews_count_text)
            info['reviews_count'] = int(reviews_count_digits.group(0)) if reviews_count_digits else 0
            # --- End of updated logic ---

            info['description'] = "\n".join(
                await page.locator(SELECTORS['product']['description_list']).all_inner_texts()
            )
            info['scraped_at'] = datetime.datetime.now()
            return info
        except Exception as e:
            log.error("Could not extract all product information. Some fields may be missing.", exc_info=True)
            # Return partial info if something went wrong
            return info

    @staticmethod
    async def parse_review(item):
        """Parses a single review item to extract its details."""
        try:
            rating = 0
            rating_class = await item.locator(SELECTORS['reviews']['rating_icon']).get_attribute('class')
            if rating_class:
                match = re.search(r'rating-(\d+)', rating_class)
                if match:
                    rating = int(match.group(1))

            review_data = {
                'reviewer_name': await item.locator(SELECTORS['reviews']['author']).inner_text(),
                'rating': rating,
                'review_title': await item.locator(SELECTORS['reviews']['title']).inner_text(),
                'review_body': await item.locator(SELECTORS['reviews']['comment_body']).inner_text(),
                'date_of_review': await item.locator(SELECTORS['reviews']['date']).inner_text(),
                'verified_buyer': 'Yes' if await item.locator(
                    SELECTORS['reviews']['verified_badge']).is_visible() else 'No'
            }
        except Exception as e:
            log.info(f"Skipping a review due to an extraction error: {e}")
            return None
        return review_data