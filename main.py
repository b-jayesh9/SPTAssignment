import asyncio
from web_scraper.config import BASE_URLS
from web_scraper.scraper import WebScraper
from duck_db.database import Database
import logging

log = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the scraper."""
    logger = logging.getLogger()
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # We will stream logs to stdout and also write logs to a log file.

    # 1. Create a handler to write logs to a file
        file_handler = logging.FileHandler('./logs/scraper.log', mode='w')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 2. Create a handler to stream logs to the console
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)


async def scrape_page(url: str, db: Database):
    """
    This function will scrape a single product page and store its data.
    It's a complete package, you know? Handles everything for one URL.
    """
    log.info(f"Starting scraper for URL: {url}")
    scraper = WebScraper(url)
    try:
        if await scraper.navigate_to_page():
            product_info = await scraper.get_product_info()

            if product_info and product_info.get('title'):
                product_id = db.upsert_product(product_info, url=url)
                log.info(f"Product '{product_info['title']}' data saved with ID: {product_id}")

                reviews = await scraper.get_reviews()
                if reviews:
                    for review in reviews:
                        db.upsert_review(review, product_id)
                    log.info(f"Successfully saved {len(reviews)} reviews for product ID: {product_id}")
                else:
                    log.info(f"No reviews were extracted for {url}.")
            else:
                log.info(f"Failed to extract essential product information from {url}. Aborting.")

    except Exception as e:
        log.error(f"A fatal error occurred while scraping {url}: {e}")

    finally:
        # Ensure all resources are always cleaned up
        await scraper.close()
        log.info(f"Scraper finished for URL: {url}")


async def main():
    """
    Our main function, but now it's a manager! It will start all the scraping jobs
    and wait for them to finish. Proper parallel processing, dekh lo!
    """
    setup_logging()
    log.info("Starting the parallel scraper job.")
    db = Database()

    # We create a list of tasks, one for each URL.
    tasks = [scrape_page(url, db) for url in BASE_URLS]

    # asyncio.gather will run all our scraping tasks at the same time.
    await asyncio.gather(*tasks)

    db.close()
    log.info("All scraping jobs finished.")


if __name__ == '__main__':
    asyncio.run(main())