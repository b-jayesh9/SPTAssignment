# Newegg Web Scraper

This project contains a resilient web scraper designed to extract product information and customer reviews from a Newegg product page. It uses modern tools like Playwright for robust browser automation and DuckDB for efficient data storage.

The scraper is built with resilience in mind, featuring automatic retries and graceful error handling to withstand common website changes and temporary issues.

## Instructions for Running the Scraper

### 1. Environment Setup

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# 1. Navigate to the project's root directory
cd newegg_scraper_project

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install the required Python packages
pip install -r requirements.txt

# 5. Install Playwright's browser binaries (this is a one-time setup)
playwright install