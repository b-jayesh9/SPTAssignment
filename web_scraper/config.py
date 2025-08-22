BASE_URL = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
HEADLESS_MODE = False # set to true after testing
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 5

# A dictionary containing all the CSS selectors used for scraping.
SELECTORS = {
    "product": {
        "title": 'h1.product-title',
        "brand": 'div.seller-store-link strong',
        "price_container": 'div.form-option-item.is-selected',
        "reviews_link": 'div.tab-nav[data-nav="Reviews"]',
        "rating_element": 'div.product-rating > i.rating',
        "reviews_count_text": 'div.product-rating > span.item-rating-num',
        "description_list": 'div.product-bullets ul li'
    },
    "reviews": {
        "container": 'div.comments',
        "review_item": 'div.comments-cell',
        "author": 'div.comments-name',
        "rating_icon": 'i[class^="rating rating-"]',  # fetch rating from class
        "title": 'span.comments-title-content',
        "comment_body": 'div.comments-content',
        "date": 'div.comments-title > span.comments-text', # check title
        "verified_badge": 'div.comments-verified-owner',
        "next_page_button": 'a.paginations-next'
    },
    "dialogs": { # find any dialog popup and fetch its close button
        "close_promo_button": '[aria-label="close"]'
    }
}

# A list of user agents to rotate for stealth purposes.
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0'
]
