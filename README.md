# Product and Review Scraper

This project is a Python-based web scraper designed to extract detailed product information and customer reviews from a Newegg product page. It uses `playwright` for robust, stealth-based web scraping to handle anti-bot measures and stores the collected data in a `DuckDB` database for easy access and analysis.

## Features

- Stealth Scraping: Utilizes `playwright-stealth` to mimic human behavior and bypass anti-bot protections like Cloudflare.
- Resilient Extraction: Designed to handle dynamic content and pagination, ensuring all reviews are captured.
- Data Storage in local DB: Saves scraped data into a local DuckDB database, providing a structured and queryable dataset.
- Automated Setup: Includes a shell script to automate the setup process, from creating a virtual environment to installing all dependencies.

## Prerequisites

- Python 3.10 or higher
- `bash` for running the setup script (default on MacOS or Linux)

## WARNING 
This project is only visible using a US IP or VPN that provides a US IP address. I could have added a network proxy to bypass this, but that was out of scope, and a bit hard.

## Setup and Installation

The project includes a setup script that automates the installation process.

1.  **Clone the Repository**
    ```bash
    git clone b-jayesh9/SPTAssignment
    cd SPTAssignment
    ```

2.  **Run the Setup Script**
    Execute the `setup.sh` script to create a virtual environment, install the required Python packages, and download the necessary browser binaries for Playwright.
    - Need `bash` for running the setup script (standard on macOS and Linux)

    This script will:
    - Check for the `uv` package manager and install it if missing.
    - Create a virtual environment named `.venv`.
    - Install all dependencies from `requirements.txt`.
    - Download and install the browser dependencies for Playwright.

## How to Run the Scraper

1.  **Activate the Virtual Environment**
    Before running the scraper, you must activate the virtual environment created by the setup script:
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the Main Script**
    Execute the `main.py` script to start the scraping process:
    ```bash
    python main.py
    ```
    The scraper will log its progress to the console and also save detailed logs in the `./logs/scraper.log` file.

## Configuration

You can customize the scraper's behavior by modifying the `web_scraper/config.py` file:

- **`BASE_URL`**: Change this URL to scrape a different product page on Newegg.
- **`HEADLESS_MODE`**: Set to `True` to run the browser in the background without a visible UI, or `False` to monitor the process visually. By default, I've set it to False for the reviewer to assess the working of the scraper.

## Accessing the Scraped Data

The data is stored in a DuckDB database file located at `data/newegg_product.duckdb`. You can use the DuckDB CLI to query the data directly from your terminal.

1.  **Connect to the Database**
    ```bash
    duckdb data/newegg_product.duckdb
    ```

2.  **Query the Data**
    Once connected, you can use standard SQL queries to explore the data. Make sure to end each query with a semicolon (`;`).

    - **View all products:**
      ```sql
      SELECT * FROM products;
      ```

    - **View all reviews:**
      ```sql
      SELECT * FROM reviews;
      ```

    - **Count the number of reviews per rating:**
       ```sql
       SELECT rating, COUNT(*) AS review_count
       FROM reviews
       GROUP BY rating
       ORDER BY rating DESC;
       ```
    - **Exit the DuckDB CLI:**
      ```sql
      .exit
      ```
## Project Structure

```
├── duck_db/
│   ├── __init__.py
│   └── database.py       # Handles all database connections and operations.
├── logs/
│   └── scraper.log       # Log file generated during runtime.
├── web_scraper/
│   ├── __init__.py
│   ├── config.py         # Stores configuration settings and CSS selectors.
│   ├── data_parser.py    # Responsible for parsing HTML content.
│   └── scraper.py        # Core web scraping logic using Playwright.
├── .venv/                # Virtual environment directory (created by setup.sh).
├── main.py               # Main entry point to run the scraper.
├── requirements.txt      # Lists all Python dependencies.
├── setup.sh              # Automates the setup and installation process.
└── README.md             # This file.
```

## Key Design Decisions

The architecture of this scraper was designed for performance, resilience, and maintainability.

### 1. Asynchronous Scraping Framework (Playwright & asyncio)

-   **Decision:** Playwright was chosen over libraries like Selenium or BeautifulSoup, and the entire application was built on Python's `asyncio` framework.
-   **Rationale & Scalability:**
    -   **Modern Web Compatibility:** Playwright excels at handling modern, JavaScript-heavy single-page applications where content is loaded dynamically.
    -   **High Concurrency:** By leveraging `asyncio`, the scraper can manage multiple browser instances and network requests concurrently. The `main.py` script uses `asyncio.gather` to launch scraping tasks for all URLs in parallel, making the system highly scalable for scraping hundreds or thousands of pages efficiently. This is a significant performance advantage over traditional synchronous scraping methods.

### 2. In-Process Analytical Database (DuckDB)

-   **Decision:** DuckDB was selected as the data storage backend instead of a traditional client-server database (like PostgreSQL) or a simple file format (like CSV).
-   **Rationale & Scalability:**
    -   **Zero-Overhead Setup:** As a file-based, in-process database, DuckDB requires no separate server or complex configuration, making the project highly portable and easy to set up.
    -   **Analytical Power:** It provides the full power of an analytical SQL database, allowing for complex queries and aggregations directly on the stored data.
    -   **Data Integrity:** The `database.py` module implements an `upsert` strategy with `UNIQUE` constraints. This ensures that re-running the scraper updates existing records (e.g., price changes) and adds new ones without creating duplicates, which is critical for maintaining a clean dataset over time.

### 3. Anti-Bot Evasion Strategy (playwright-stealth)

-   **Decision:** `playwright-stealth` was integrated to actively combat anti-bot measures.
-   **Rationale & Scalability:**
    -   **Human-like Behavior:** Modern e-commerce sites use sophisticated fingerprinting to detect automated browsers. `playwright-stealth` automatically applies a series of patches to the browser automation scripts to evade these detection mechanisms (e.g., by hiding `webdriver` flags).
    -   **Increased Reliability:** This significantly increases the success rate of scraping operations and reduces the likelihood of being IP-blocked, making the scraper more reliable for long-running, large-scale jobs. This is further enhanced by the rotation of user agents defined in `config.py`.

### 4. Modular and Centralized Configuration

-   **Decision:** The project is structured into distinct modules (scraper, parser, database), and all configuration settings, including URLs and CSS selectors, are centralized in `web_scraper/config.py`.
-   **Rationale & Scalability:**
    -   **Maintainability:** This separation of concerns is crucial for long-term maintenance. If the target website updates its layout, changes only need to be made to the CSS selectors in the `config.py` file, without altering the core scraping or database logic.
    -   **Adaptability:** This design makes it easy to adapt the scraper for a different website. A new configuration file and potentially a new parser function could be added without refactoring the entire application.

# Bonus Assignment
The bonus assignment can be found at the following repository:
[https://github.com/b-jayesh9/SPTBonusAssignment](https://github.com/b-jayesh9/SPTBonusAssignment)