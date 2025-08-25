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

├── duck_db/
│   ├── database.py       # Handles all database connections and operations.
│   └── __init__.py
├── logs/
│   └── scraper.log       # Log file generated during runtime.
├── web_scraper/
│   ├── config.py         # Stores configuration settings and CSS selectors.
│   ├── data_parser.py    # Responsible for parsing HTML content.
│   ├── scraper.py        # Core web scraping logic using Playwright.
│   └── __init__.py
├── main.py               # Main entry point to run the scraper.
├── requirements.txt      # Lists all Python dependencies.
├── setup.sh              # Automates the setup and installation process.
└── README.md             # This file.


## Considerations and Design Decisions
### Scraping Framework
For the scraping framework, I went with Playwright because of how well it handles modern websites that rely heavily on JavaScript.
Unlike older tools, Playwright's asynchronous design makes it much faster when dealing with multiple web requests,
which is something that BeautifulSoup or Selenium do not provide.
### Database Selection
I chose DuckDB as the backend database, and it turned out to be perfect for this project.
Since it's file-based and doesn't require running a separate database server, setup is easy.
You get all the analytical power of SQL without the overhead of managing a traditional database system.
### Handling Anti-Bot Protection
Most e-commerce sites like Newegg use Cloudflare and similar services to detect and block automated scrapers.
To get around this, I integrated playwright-stealth, which applies various techniques to make the scraper's behavior more human-like.
This dramatically improved the success rate when accessing protected pages.
### Code Organization
I structured the project with a clear separation between different concerns: the scraper logic, data parsing, and database operations are all in separate modules.
This approach makes maintenance much easier since changes to one part don't ripple through the entire codebase.
If Newegg changes their page layout tomorrow, I only need to update the CSS selectors in the parser module.

### Configuration Management
Rather than scattering settings and selectors throughout the code, everything configurable lives in a single config file. This makes it much easier to tweak the scraper's behavior or adapt it to different sites without hunting through multiple files.
### Setup Automation
The setup script handles all the tedious initial configuration - setting up the virtual environment, installing dependencies, and downloading browser binaries. This removes a lot of friction for anyone who wants to run or modify the scraper.



# BONUS ASSIGNMENT

Link to the bonus assignment : https://github.com/b-jayesh9/SPTBonusAssignment