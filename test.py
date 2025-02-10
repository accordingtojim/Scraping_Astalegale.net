from scraping import fetch_html_with_cookies

import time
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def fetch_html_with_playwright(url):
    """
    Fetch the HTML content of a webpage using Playwright with a browser.

    :param url: URL of the webpage to fetch.
    :return: The HTML content as a string or None if an error occurs.
    """
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)  # Open Firefox browser
            context = browser.new_context()

            # Open a new page
            page = context.new_page()

            # Navigate to the URL
            print(f"Navigating to: {url}")
            page.goto(url, timeout=60000)

            # Wait for the page to load completely
            time.sleep(random.uniform(3, 5))

            # Get the HTML content
            html_content = page.content()

            # Close the browser
            browser.close()

            return html_content
    except Exception as e:
        print(f"⚠️ Error fetching page with Playwright: {e}")
        return None

# Test the function with a single link
if __name__ == "__main__":
    test_url = "https://www.idealista.it/affitto-case/roma-roma/"
    html = fetch_html_with_playwright(test_url)
    if html:
        print("HTML fetched successfully.")
        soup = BeautifulSoup(html, 'html.parser')
        print(soup.prettify()[:1000])  # Print a preview of the HTML content
    else:
        print("Failed to fetch HTML.")
