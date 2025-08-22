import duckdb
import logging
import os

log = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the scraper."""

    def __init__(self, db_name='../data/newegg_product.duckdb'):
        try:
            # Get the full path and ensure the directory exists before connecting
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_name))
            db_dir = os.path.dirname(db_path)
            os.makedirs(db_dir, exist_ok=True)

            self.connection = duckdb.connect(db_path)
            self.cursor = self.connection.cursor()
            self.create_tables()
            log.info(f"Successfully connected to database: {db_path}")
        except Exception as e:
            log.critical("Failed to connect to or initialize the database.", exc_info=True)
            raise

    def create_tables(self):
        """
        Creates the 'products' and 'reviews' tables with UNIQUE constraints
        to prevent duplicate entries.
        """
        try:
            # Create products table with a unique constraint on the URL.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id              INTEGER PRIMARY KEY,
                    url             VARCHAR UNIQUE NOT NULL,
                    title           VARCHAR,
                    brand           VARCHAR,
                    price           VARCHAR,
                    ratings         VARCHAR,
                    reviews_count   INTEGER,
                    description     TEXT,
                    scraped_at      TIMESTAMP DEFAULT current_timestamp
                );
            """)

            # Create reviews table with a foreign key to the products table.
            # A composite unique key ensures that the same review isn't inserted twice.
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id              INTEGER PRIMARY KEY,
                    product_id      INTEGER,
                    reviewer_name   VARCHAR,
                    rating          INTEGER,
                    review_title    VARCHAR,
                    review_body     TEXT,
                    date_of_review  VARCHAR,
                    verified_buyer  VARCHAR,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE (product_id, reviewer_name, date_of_review)
                );
            """)

            self.connection.commit()
            log.info("Tables 'products' and 'reviews' are ready.")
        except Exception as e:
            log.error("Error creating database tables.", exc_info=True)

    def upsert_product(self, product_info, url):
        """
        Inserts a new product or updates an existing one based on the URL.
        Returns the product's ID.
        """
        check_sql = "SELECT id FROM products WHERE url = ?"
        try:
            existing = self.cursor.execute(check_sql, (url,)).fetchone()

            if existing:
                # If the product exists, update its details.
                update_sql = """
                    UPDATE products
                    SET price = ?,
                        ratings = ?,
                        reviews_count = ?,
                        scraped_at = current_timestamp
                    WHERE url = ?
                """
                update_data = (
                    product_info['price'],
                    product_info['ratings'],
                    product_info['reviews_count'],
                    url
                )
                self.cursor.execute(update_sql, update_data)
                self.connection.commit()
                product_id = existing[0]
                log.info(f"Updated existing product '{product_info['title']}' with ID: {product_id}")
                return product_id
            else:
                # If the product does not exist, insert a new record.
                # Manually get the next ID for the new product.
                next_id_sql = "SELECT COALESCE(MAX(id), 0) + 1 FROM products"
                next_id = self.cursor.execute(next_id_sql).fetchone()[0]

                insert_sql = """
                    INSERT INTO products (
                        id, url, title, brand, price, ratings, reviews_count, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                product_data = (
                    next_id,
                    url,
                    product_info['title'],
                    product_info['brand'],
                    product_info['price'],
                    product_info['ratings'],
                    product_info['reviews_count'],
                    product_info['description']
                )
                self.cursor.execute(insert_sql, product_data)
                self.connection.commit()

                log.info(f"Inserted new product '{product_info['title']}' with ID: {next_id}")
                return next_id
        except Exception as e:
            log.error(f"Failed to upsert product: {product_info.get('title')}", exc_info=True)
            return None

    def upsert_review(self, review_info, product_id):
        """
        Inserts a new review only if it doesn't already exist.
        """
        try:
            # A product_id of None would cause an error, so we check for it.
            if product_id is None:
                log.warning(f"Skipping review by {review_info.get('reviewer_name')} because product_id is None.")
                return

            # Check if review already exists.
            check_sql = """
                SELECT id
                FROM reviews
                WHERE product_id = ?
                  AND reviewer_name = ?
                  AND date_of_review = ?
            """
            existing = self.cursor.execute(check_sql, (
                product_id,
                review_info['reviewer_name'],
                review_info['date_of_review']
            )).fetchone()

            if existing:
                log.debug(f"Review by {review_info['reviewer_name']} already exists, skipping.")
                return

            # Get the next available ID for the new review.
            next_id_sql = "SELECT COALESCE(MAX(id), 0) + 1 FROM reviews"
            next_id = self.cursor.execute(next_id_sql).fetchone()[0]

            # Insert the new review.
            insert_sql = """
                INSERT INTO reviews (
                    id, product_id, reviewer_name, rating, review_title, review_body,
                    date_of_review, verified_buyer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            review_data = (
                next_id,
                product_id,
                review_info['reviewer_name'],
                review_info['rating'],
                review_info['review_title'],
                review_info['review_body'],
                review_info['date_of_review'],
                review_info['verified_buyer']
            )
            self.cursor.execute(insert_sql, review_data)
            self.connection.commit()
            log.debug(f"Inserted review by {review_info['reviewer_name']} with ID: {next_id}")
        except Exception as e:
            log.warning(f"Failed to upsert review by {review_info.get('reviewer_name')}", exc_info=True)

    def close(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            log.info("Database connection closed.")
