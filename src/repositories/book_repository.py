from sqlalchemy import text

from config import db
from entities.book import Book


def get_books():
    query = text(
        "SELECT id, title, author, year, publisher, address FROM book")
    result = db.session.execute(query)
    books = result.fetchall()
    return [Book(book[0], book[1], book[2], book[3], book[4], book[5]) for book in books]
