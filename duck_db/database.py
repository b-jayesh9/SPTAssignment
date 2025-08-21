import duckdb
import os

class Database:
    """Manages the DuckDB database for storing scraped data."""
    def __init__(self, db_name='../data/newegg_product.duckdb'):
        """Initializes the database connection and creates tables."""
        # Ensures the DB file is created inside the 'web_scraper' directory
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.conn = duckdb.connect(db_path)
        print(f"Database connected at: {db_path}")
        self.create_tables()

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id UBIGINT PRIMARY KEY,
            title VARCHAR,
            brand VARCHAR,
            price VARCHAR,
            ratings VARCHAR,
            reviews_count INTEGER,
            description VARCHAR
        )
        ''')
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id UBIGINT PRIMARY KEY,
            product_id UBIGINT,
            reviewer_name VARCHAR,
            rating INTEGER,
            review_title VARCHAR,
            review_body VARCHAR,
            date_of_review VARCHAR,
            verified_buyer VARCHAR
        )
        ''')
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_products START 1;")
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_reviews START 1;")

    def insert_product(self, product_info):
        """Inserts a product into the database and returns its ID."""
        product_id = self.conn.execute("SELECT nextval('seq_products')").fetchone()[0]
        self.conn.execute('''
        INSERT INTO products (id, title, brand, price, ratings, reviews_count, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_id, product_info.get('title'), product_info.get('brand'),
            product_info.get('price'), product_info.get('ratings'),
            product_info.get('reviews_count'), product_info.get('description')
        ))
        return product_id

    def insert_review(self, review, product_id):
        """Inserts a review linked to a product."""
        review_id = self.conn.execute("SELECT nextval('seq_reviews')").fetchone()[0]
        self.conn.execute('''
        INSERT INTO reviews (id, product_id, reviewer_name, rating, review_title, review_body, date_of_review, verified_buyer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            review_id, product_id, review.get('reviewer_name'), review.get('rating'),
            review.get('review_title'), review.get('review_body'),
            review.get('date_of_review'), review.get('verified_buyer')
        ))

    def close(self):
        """Closes the database connection."""
        self.conn.close()