import asyncio
from web_scraper.scraper import ResilientNeweggScraper, BASE_URL
from duck_db.database import Database


async def main():
    """Main function to orchestrate the scraping process."""
    print("--- Starting the Newegg Scraper ---")

    # Initialize the scraper and database
    scraper = ResilientNeweggScraper(BASE_URL)
    db = Database()

    try:
        if await scraper.navigate_to_page():
            print('inside')
            # Scrape product data
            product_info = await scraper.extract_product_info()
            print(product_info)
            if product_info and product_info.get('title'):
                # Save product data and get its ID
                product_id = db.insert_product(product_info)
                print(f"Product '{product_info['title']}' data saved with ID: {product_id}")

                # Scrape review data
                reviews = await scraper.extract_reviews()
                if reviews:
                    for review in reviews:
                        db.insert_review(review, product_id)
                    print(f"Successfully saved {len(reviews)} reviews.")
                else:
                    print("No reviews were extracted.")
            else:
                print("Failed to extract essential product information. Aborting.")

    except Exception as e:
        print(f"A fatal error occurred in the main process: {e}")

    finally:
        # Ensure resources are always cleaned up
        db.close()
        print("--- Scraper finished ---")


if __name__ == '__main__':
    asyncio.run(main())
