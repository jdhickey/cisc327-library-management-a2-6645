"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_db_connection, get_book_by_id, get_book_by_isbn, get_patron_borrowed_books,
    get_patron_borrow_count, insert_book, insert_borrow_record,
    update_book_availability, update_borrow_record_return_date, get_all_books,
    conn_execute_read
)
from services.payment_service import PaymentGateway

def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    if len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."

def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "This book does not exist."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    if current_borrowed > 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'

def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    Implements R4 as per requirements

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to return

    Returns:
        tuple: (success: bool, message: str)
    """
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."

    if book_id not in [book['id'] for book in get_all_books()]:
        return False, "Book not found."

    if book_id not in [book['book_id'] for book in get_patron_borrowed_books(patron_id)]:
        return False, "Book not borrowed by patron."

    if not update_borrow_record_return_date(patron_id, book_id, datetime.now()):
        return False, "Unable to update record."
    if not update_book_availability(book_id, 1):
        return False, "Unable to update book availability."

    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    if fee_info['fee_amount'] > 0:
        return True, f"Book returned successfully. Late fee: ${fee_info['fee_amount']:.2f} for {fee_info['days_overdue']} day(s) overdue"
    else:
        return True, "Book returned successfully. No late fee."

def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
        - Books due 14 days after borrowing
        - $0.50/day for first 7 days overdue
        - $1.00/day for each additional day after 7 days
        - Maximum $15.00 per book
    Implements R5 as per requirements

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow

    Returns:
        {
            'fee_amount': X.XX,
            'days_overdue': X,
            'status': 'STATUS'
        }
    """

    fee_json = {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'PENDING'
        }

    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        fee_json['status'] = 'Invalid patron ID'
        return fee_json

    book_exists = conn_execute_read('SELECT 1 FROM books WHERE id = ?', (book_id,))
    if not book_exists:
        fee_json['status'] = 'Book not found'
        return fee_json

    record_list = conn_execute_read('''
        SELECT borrow_date, due_date, return_date
        FROM borrow_records
        WHERE patron_id = ? AND book_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (patron_id, book_id,))
    record = record_list[0] if record_list else None

    if not record:
        fee_json['status'] = 'No corresponding borrow record found'
        return fee_json

    due_date = datetime.fromisoformat(record['due_date'])
    return_date = datetime.fromisoformat(record['return_date']) if record['return_date'] else datetime.now()

    days_overdue = max(0, (return_date.date() - due_date.date()).days)
    if days_overdue <= 0:
        fee_json['status'] = 'On time'
        return fee_json

    if days_overdue <= 7:
        fee = days_overdue * 0.50
    else:
        fee = (7 * 0.50) + (days_overdue - 7) * 1.00
    fee = min(fee, 15.00)

    fee_json['fee_amount'], fee_json['days_overdue'], fee_json['status'] = round(fee, 2), days_overdue, 'Overdue'
    return fee_json

def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    Implements R6 as per requirements

    Args:
        search_term: a string containing the search content
        search_type: author, title, or isbn

    Returns:
        List[Dict]: [
            {'id': X, 'title': 'X', 'author': 'X', 'isbn': X, 'total_copies': X, 'available_copies': X},
            {'id': Y, 'title': 'Y', 'author': 'Y', 'isbn': Y, 'total_copies': Y, 'available_copies': Y}...
        ]
    """

    query = ""
    param = ""

    if search_type == 'title':
        query = "SELECT * FROM books WHERE title LIKE ? ORDER BY title"
        param = f"%{search_term}%"
    elif search_type == 'author':
        query = "SELECT * FROM books WHERE author LIKE ? ORDER BY title"
        param = f"%{search_term}%"
    elif search_type == 'isbn':
        query = "SELECT * FROM books WHERE isbn = ? ORDER BY title"
        param = search_term
    else:
        return []

    return conn_execute_read(query, (param,))

def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    Implements R7 as per requirements

    Args:
        patron_id: 6-digit library card ID

    Returns:
        Dict: {
            "status": "STATUS",
            "patron_id": XXXXXX,
            "currently_borrowed_count": X,
            "currently_borrowed_books": List[Dict],
            "total_late_fees": X.XX,
            "borrowing_history": List[Dict]
        }
    """
    return_block = {
        "status": "default",
        "patron_id": None,
        "currently_borrowed_count": 0,
        "currently_borrowed_books": 0,
        "total_late_fees": 0,
        "borrowing_history": None
    }

    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return_block['status'] = "Invalid patron ID"
        return return_block

    current = get_patron_borrowed_books(patron_id)

    total_late_fees = 0.0
    for book in current:
        fee_info = calculate_late_fee_for_book(patron_id, book['book_id'])
        total_late_fees += fee_info['fee_amount']

    count = get_patron_borrow_count(patron_id)

    history = conn_execute_read('''
        SELECT b.title, b.author, br.borrow_date, br.due_date, br.return_date
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        WHERE br.patron_id = ?
        ORDER BY br.borrow_date DESC
    ''', (patron_id,))

    return_block['status'] = "success"
    return_block['patron_id'] = patron_id
    return_block['currently_borrowed_count'] = count
    return_block['currently_borrowed_books'] = current
    return_block['total_late_fees'] = round(total_late_fees, 2)
    return_block['total_late_fees'] = history

    return return_block


def pay_late_fees(patron_id: str, book_id: int,
                  payment_gateway: PaymentGateway = None) -> Tuple[
    bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.

    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.

    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)

    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])

    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None

    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)

    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None

    fee_amount = fee_info.get('fee_amount', 0.0)

    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None

    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None

    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()

    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )

        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None

    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None


def refund_late_fee_payment(transaction_id: str, amount: float,
                            payment_gateway: PaymentGateway = None) -> Tuple[
    bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).

    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking

    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)

    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."

    if amount <= 0:
        return False, "Refund amount must be greater than 0."

    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."

    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()

    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id,
                                                          amount)

        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"

    except Exception as e:
        return False, f"Refund processing error: {str(e)}"