from flask import Blueprint, jsonify, request
from utils.MongoUtility import Book  # Import the Book model
from bson import ObjectId

# Create a Flask Blueprint for book-related routes
book_endpoints = Blueprint('book_endpoints', __name__)


@book_endpoints.route('/get_all_books', methods=['GET'])
def get_all_books():
    """
    Endpoint to fetch all books in the database.
    """
    try:
        # Fetch all books from the database
        books = Book.objects()

        # Convert book objects to a list of dictionaries
        books_data = []
        for book in books:
            publication_date = book.publication_date
            if isinstance(publication_date, str):
                formatted_date = publication_date  # Use the string directly
            elif publication_date:
                formatted_date = publication_date.strftime('%Y-%m-%d')  # Format datetime object
            else:
                formatted_date = None  # Handle missing dates

            books_data.append({
                "book_id": str(book.id),
                "title": book.title,
                "author": book.author,
                "genre": book.genre,
                "publication_date": formatted_date,
                "isbn": book.isbn,
                "availability_status": book.availability_status,
                "media_type": book.media_type,
            })

        # Return the list of books as a JSON response
        return jsonify({"books": books_data}), 200

    except Exception as e:
        # Handle exceptions and return an error response
        return jsonify({"error": str(e)}), 500


@book_endpoints.route('/get_book/<book_id>', methods=['GET'])
def get_book_by_id(book_id):
    """
    Endpoint to fetch a specific book by either ObjectId or custom book_id.
    """
    try:
        # Try to convert book_id to ObjectId
        try:
            book = Book.objects(id=ObjectId(book_id)).first()
        except Exception:
            # If the book_id isn't a valid ObjectId, try by custom book_id field
            book = Book.objects(book_id=book_id).first()

        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Format the publication_date if present
        publication_date = book.publication_date
        if isinstance(publication_date, str):
            formatted_date = publication_date
        elif publication_date:
            formatted_date = publication_date.strftime('%Y-%m-%d')
        else:
            formatted_date = None

        # Create a dictionary of the book's details
        book_data = {
            "book_id": str(book._id),
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "publication_date": formatted_date,
            "isbn": book.isbn,
            "availability_status": book.availability_status,
            "media_type": book.media_type,
        }

        # Return the book details
        return jsonify(book_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
