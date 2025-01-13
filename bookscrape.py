
import requests
from bs4 import BeautifulSoup
import pandas as pd

BASE_URL = "http://books.toscrape.com/"
CATALOG_URL = "http://books.toscrape.com/catalogue/"


def get_book_details(book_url):
    """
    Extracts book details from the individual book page.

    Args:
        book_url: URL of the individual book page.

    Returns:
        A dictionary containing book details.
    """
    book_details_response = requests.get(f"{CATALOG_URL}{book_url}")
    # book_details_response.raise_for_status()

    book_details_soup = BeautifulSoup(book_details_response.content, 'html.parser')

    # Extract UPC (may not be available for all books)
    upc_element = book_details_soup.find('th', string='UPC')
    upc = upc_element.find_next_sibling('td') if upc_element else None
    upc = upc.get_text().strip() if upc else 'NA'

    # Extract tax (may not be available)
    tax_element = book_details_soup.find('th', string='Tax')
    tax = tax_element.find_next_sibling('td') if tax_element else None
    tax = tax.get_text().strip() if tax else 'NA'

    # Extract number of reviews (may not be available)
    review_count_element = book_details_soup.find('p', class_='star-rating')
    review_count = review_count_element.find('a') if review_count_element else None
    review_count = review_count.get_text().strip() if review_count else '0'

    # Extract description
    product_description_element = book_details_soup.findAll('p')
    description = product_description_element[3].get_text()[0:99]


    # Extract category and category link from the book page (if available)
    breadcrumb_list = book_details_soup.find('ul', class_='breadcrumb')
    if breadcrumb_list:
        category_url = breadcrumb_list.find_all('li')[-2].a['href']
        category_link = BASE_URL + category_url[3:]
        category = breadcrumb_list.find_all('li')[-2].a.text.strip()
    else:
        category = 'Unknown'
        category_link = 'Unknown'

    return {
        "Book_UPC": upc,
        "Book_Tax": tax,
        "Book_number_of_reviews": review_count,
        "Category": category,
        "Category_link": category_link,
        "Book_description": description
    }



def get_books_from_page(soup):
    """Extract book data from a single page.

    Args:
        soup: The BeautifulSoup object representing the parsed HTML content.

    Returns:
        A list of dictionaries, where each dictionary contains information about a book.
    """

    books = []
    for book in soup.find_all('article', class_='product_pod'):
        # Extract book details
        title_element = book.h3.a
        title = title_element.get_attribute_list('title')[0]
        book_link = title_element['href']

        availability = book.find('p', class_='instock availability').text.strip()

        price = book.find('p', class_='price_color').text.replace('Â', '').strip()

        # Get book details from the individual book page
        book_details = get_book_details(book_link)
        book_details_url = f"{CATALOG_URL}{book_link}"

        books.append({
            "Book_name": title,
            "Book_link": book_details_url,
            "Book_stock_availability": availability,
            "Book_price": price,
            **book_details  # Merge book details dictionary
        })

    return books


def scrape_books(base_url):
    """Scrape all book data from the website."""

    all_books = []
    next_page = "catalogue/page-1.html"

    while next_page:
        response = requests.get(f"{base_url}/{next_page}")
        if response.status_code != 200:
            print(f"Failed to fetch page: {next_page}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        all_books.extend(get_books_from_page(soup))

        # Find the next page link
        next_button = soup.find("li", class_="next")
        next_page = next_button.a["href"] if next_button else None
        if next_page:  # Update the next page link to include the correct path
            next_page = f"catalogue/{next_page}"

    return all_books

# Run the scraping function
books = scrape_books(BASE_URL)

# Create a DataFrame from the scraped data
df = pd.DataFrame(books)

# Optionally save the DataFrame to a CSV file
df.to_csv("books.csv", index=False)

print("Data saved to books.csv")
