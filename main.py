import asyncio
from web_scraper.config import BASE_URL
from web_scraper.scraper import WebScraper
from duck_db.database import Database # This imports the database
import logging

log = logging.getLogger(__name__)

def setup_logging():
    """Configure logging for the scraper."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # default level should be INFO

    # Create a formatter to define the log message structure
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # WE will stream logs to stdout, and also write logs to a log file.

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



async def main():
    """Main function to orchestrate the scraping and database insertion process."""
    # setup logging
    setup_logging()

    log.info("Starting the Scraper")

    # Initialize the scraper and database
    scraper = WebScraper(BASE_URL)
    db = Database()

    try:
        if await scraper.navigate_to_page():
            # Scrape product data using the updated method name
            product_info = await scraper.get_product_info()

            if product_info and product_info.get('title'):
                # Save product data and get its ID
                product_id = db.upsert_product(product_info, url=BASE_URL)
                log.info(f"Product '{product_info['title']}' data saved with ID: {product_id}")

                # Scrape review data using the updated method name
                reviews = await scraper.get_reviews()
                if reviews:
                    # Insert each review into the database
                    for review in reviews:
                        db.upsert_review(review, product_id)
                    log.info(f"Successfully saved {len(reviews)} reviews.")
                else:
                    log.info("No reviews were extracted.")
            else:
                log.info("Failed to extract essential product information. Aborting.")

    except Exception as e:
        log.error(f"A fatal error occurred in the main process: {e}")

    finally:
        # Ensure all resources are always cleaned up
        await scraper.close()
        db.close()
        log.info("Scraper finished")


if __name__ == '__main__':
    asyncio.run(main())