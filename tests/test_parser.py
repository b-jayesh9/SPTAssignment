import pytest
import re
from playwright.async_api import async_playwright
from pathlib import Path
from web_scraper.data_parser import DataParser


# A pytest fixture to load the HTML content once for all tests in this file
@pytest.fixture(scope="module")
def html_content():
    """Loads the static HTML file."""
    path = Path(__file__).parent /"fixtures"/"product_page.html"
    return path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_extract_product_info_happy_path(html_content):
    """
    Tests if the parser can correctly extract all required fields
    from a known, valid HTML file.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Load  static HTML content into the mock page
        await page.set_content(html_content)

        # Run parser on the mock page
        product_info = await DataParser.extract_product_info(page)

        await browser.close()

        # Assert that the extracted data is correct
        assert product_info is not None
        assert "AMD Ryzen 7 9800X" in product_info['title']
        assert product_info['brand'] == "AMD"
        assert product_info['price'] == "$479.00"
        assert "4.8 out of 5 eggs" in product_info['ratings']
        assert product_info['reviews_count'] == 484
        assert "CES 2025 Innovation" in product_info['description']


@pytest.mark.asyncio
async def test_extract_product_info_missing_title(html_content):
    """
    Tests how the parser handles a missing product title element (h1.product-title).

    This is a critical failure case. If the title is missing, the scraper
    should fail gracefully. The test verifies that the returned 'title'
    is None or missing, indicating a failure to parse the essential data.
    """
    pattern = re.compile(r'<h1 class="product-title".*?</h1>', re.DOTALL)
    html_without_title = re.sub(pattern, '', html_content)

    # check to ensure our HTML modification was successful.
    assert '<h1 class="product-title"' not in html_without_title

    #  Run the parser on the modified HTML.
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Load the HTML that is guaranteed to be missing the title.
        await page.set_content(html_without_title)

        product_info = await DataParser.extract_product_info(page)
        await browser.close()

    assert 'title' not in product_info or product_info['title'] is None


# Similar tests can be written for other parts of the parser.