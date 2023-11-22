from bs4 import BeautifulSoup
import requests
import json
import time
from urllib.request import urlopen
from requests.exceptions import HTTPError, RequestException


class Book:
    def __init__(self, title, author, release_date, price, score, genres):
        self.title = title
        self.author = author
        self.release_date = release_date
        self.price = price
        self.score = score
        self.genres = genres


def scrape_title(book_url_content):
    book_title_element = book_url_content.find("h1", {"data-testid": "bookTitle"})

    if book_title_element is not None:
        return book_title_element.get_text().strip()
    else:
        print("Error: No se pudo encontrar el título.")
        return None


def scrape_author(book_url_content):
    author_element = book_url_content.find("span", {"data-testid": "name"})

    if author_element is not None:
        return author_element.get_text().strip()
    else:
        print("Error: No se pudo encontrar el autor.")
        return None


def scrape_release(book_url_content):
    publication_info_element = book_url_content.find("p", {"data-testid": "publicationInfo"})

    if publication_info_element is not None:
        bookRelease = publication_info_element.get_text()
        bookRelease = bookRelease.strip()

        aux = bookRelease.replace(',', '')
        meses = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8,
                 'September': 9, 'October': 10, 'November': 11, 'December': 12}
        aux = aux.split(' ')
        for i in range(len(aux)):
            if aux[i] not in meses and not aux[i].isdigit():
                aux[i] = None
            elif aux[i] in meses:
                aux[i] = meses[aux[i]]
            else:
                aux[i] = int(aux[i])
        while None in aux:
            aux.pop(aux.index(None))

        return aux
    else:
        print("Error: No se pudo encontrar la información de publicación.")
        return None


def scrape_price(book_url_content):
    bookScore = str(book_url_content.findAll("div", {"class": "BookActions"}))
    string = ''
    for i in range(len(bookScore)):
        if bookScore[i] == '$':
            string += bookScore[i + 1] + bookScore[i + 2] + bookScore[i + 3] + bookScore[i + 4]
            if bookScore[i + 5].isdigit():
                string += bookScore[i + 5]
            aux = string.strip()
            return float(aux)

    if len(string) == 0:
        return 0


def scrape_score(book_url_content):
    rating_element = book_url_content.find("div", {"class": "RatingStatistics__rating"})

    if rating_element is not None:
        bookScore = rating_element.get_text().strip()

        return float(bookScore)
    else:
        print("Error: No se pudo encontrar la puntuación.")
        return None


def scrape_genres(book_url_content):
    bookGenres = book_url_content.findAll("span", {"class": "BookPageMetadataSection__genreButton"})
    list_genre = [genre.find("a", {"class": "Button Button--tag-inline Button--small"}).get_text() for genre in bookGenres]
    return list_genre


def get_book_info(book_url):
    content = urlopen(book_url)
    bs = BeautifulSoup(content.read(), 'html.parser')

    title = scrape_title(bs)
    author = scrape_author(bs)
    release_date = scrape_release(bs)
    price = scrape_price(bs)
    score = scrape_score(bs)
    genres = scrape_genres(bs)

    return Book(title, author, release_date, price, score, genres)


def save_books_data(books, json_filename):
    try:
        with open(json_filename, 'r') as json_file:
            existing_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    valid_books = [book for book in books if all([book.title, book.author, book.release_date])]

    existing_data.extend(valid_books)

    def book_serializer(obj):
        if isinstance(obj, Book):
            return obj.__dict__
        return obj

    with open(json_filename, "w") as json_file:
        json.dump(existing_data, json_file, indent=4, default=book_serializer)


def GoodreadsScraper():
    base_url = "https://www.goodreads.com"

    json_filename = "all_books.json"

    max_retries = 3

    for page_number in range(1, 4):
        print(page_number)
        start_url = f"https://www.goodreads.com/list/show/264.Books_That_Everyone_Should_Read_At_Least_Once?page={page_number}"
        print(start_url)
        for retry in range(max_retries):
            try:
                response = requests.get(start_url)
                response.raise_for_status()
                break
            except HTTPError as errh:
                print(f"Error HTTP en la página {page_number} - Intento {retry + 1}/{max_retries}: {errh}")
            except RequestException as err:
                print(f"Error de conexión en la página {page_number} - Intento {retry + 1}/{max_retries}: {err}")
            except Exception as e:
                print(f"Error desconocido en la página {page_number} - Intento {retry + 1}/{max_retries}: {e}")

            time.sleep(10)

        else:
            print(f"La página {page_number} no pudo ser recuperada después de {max_retries} intentos. Omitiendo.")

        html = response.content
        soup = BeautifulSoup(html, 'html.parser')

        book_urls = [base_url + a['href'] for a in soup.find_all('a', class_='bookTitle')]

        books = []
        for book_url in book_urls:
            book_info = get_book_info(book_url)
            books.append(book_info)

        save_books_data(books, json_filename)


if __name__ == "__main__":
    GoodreadsScraper()
