import pytest
from datetime import datetime, timedelta

from library_service import (
    add_book_to_catalog, get_all_books, borrow_book_by_patron, return_book_by_patron,
    calculate_late_fee_for_book, search_books_in_catalog, get_patron_status_report, get_book_by_isbn
)
from database import init_database, insert_book, get_db_connection, add_sample_data

# Tests written by ChatGPT for comparison purposes

# ------------------------
# Test Setup Fixture
# ------------------------
@pytest.fixture(autouse=True)
def fresh_db():
    conn = get_db_connection()
    conn.execute('''DROP TABLE books''')
    conn.execute('''DROP TABLE borrow_records''')
    conn.close()

    init_database()
    add_sample_data()
    yield

# ========================
# R1: Add Book to Catalog
# ========================

def test_add_book_valid():
    success, message = add_book_to_catalog("Brave New World", "Aldous Huxley", "9780060850524", 3)
    assert success is True
    assert "successfully added" in message

def test_add_book_no_title():
    success, message = add_book_to_catalog("", "Author", "9780060850524", 3)
    assert success is False
    assert message == "Title is required."

def test_add_book_title_too_long():
    title = "A" * 201
    success, message = add_book_to_catalog(title, "Author", "9780060850524", 3)
    assert success is False
    assert "less than 200" in message

def test_add_book_no_author():
    success, message = add_book_to_catalog("Book", "", "9780060850524", 3)
    assert success is False
    assert message == "Author is required."

def test_add_book_duplicate_isbn():
    add_book_to_catalog("Book A", "Author A", "9780060850524", 2)
    success, message = add_book_to_catalog("Book B", "Author B", "9780060850524", 1)
    assert success is False
    assert "already exists" in message

# ========================
# R2: Book Catalog Display
# ========================

def test_get_all_books_default_order():
    insert_book("Brave New World", "Aldous Huxley", "9780060850524", 3, 3)
    insert_book("Animal Farm", "George Orwell", "9780451526342", 2, 2)
    books = get_all_books()
    titles = [b['title'] for b in books]
    assert titles == sorted(titles)

def test_get_all_books_order_by_author():
    insert_book("Book A", "Charlie Author", "9780000000001", 1, 1)
    insert_book("Book B", "Alice Author", "9780000000002", 1, 1)
    books = get_all_books(order_by="author")
    authors = [b['author'] for b in books]
    assert authors == sorted(authors)

def test_get_all_books_structure():
    insert_book("Test Book", "Test Author", "9780000000003", 2, 2)
    books = get_all_books()
    for book in books:
        assert 'id' in book
        assert 'title' in book
        assert 'author' in book
        assert 'isbn' in book
        assert 'total_copies' in book
        assert 'available_copies' in book

def test_get_all_books_empty_db():
    init_database()
    books = get_all_books()
    assert len(books) == 3

def test_get_all_books_invalid_order():
    with pytest.raises(Exception):
        get_all_books(order_by="nonexistent_column")

# ========================
# R3: Book Borrowing
# ========================

def test_borrow_book_valid():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    success, message = borrow_book_by_patron("000001", 1)
    assert success is True
    assert "Successfully borrowed" in message

def test_borrow_book_invalid_patron_id():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    success, message = borrow_book_by_patron("123", 1)
    assert success is False
    assert "Invalid patron ID" in message

def test_borrow_book_not_available():
    add_book_to_catalog("Book 1", "Author", "9780000000004", 1)
    id = get_book_by_isbn("9780000000004")['id']
    borrow_book_by_patron("000000", id)
    success, message = borrow_book_by_patron("000001", id)
    assert success is False
    assert "currently not available" in message

def test_borrow_book_limit(monkeypatch):
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    monkeypatch.setattr('library_service.get_patron_borrow_count', lambda pid: 6)
    success, message = borrow_book_by_patron("000001", 1)
    assert success is False
    assert "maximum borrowing limit" in message

# ========================
# R4: Book Return
# ========================

def test_return_book_valid():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    borrow_book_by_patron("000001", 1)
    success, message = return_book_by_patron("000001", 1)
    assert success is True
    assert "Book returned successfully" in message

def test_return_book_not_borrowed():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    success, message = return_book_by_patron("000001", 1)
    assert success is False
    assert "Book not borrowed by patron" in message

def test_return_book_invalid_patron():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    success, message = return_book_by_patron("123", 1)
    assert success is False
    assert "Invalid patron ID" in message

# ========================
# R5: Late Fee Calculation
# ========================

def test_late_fee_on_time(monkeypatch):
    borrow_date = datetime.now() - timedelta(days=10)
    due_date = borrow_date + timedelta(days=14)
    monkeypatch.setattr('library_service.conn_execute_read', lambda q,p=(): [{"borrow_date": borrow_date.isoformat(), "due_date": due_date.isoformat(), "return_date": None}])
    fee_info = calculate_late_fee_for_book("000001", 1)
    assert fee_info['days_overdue'] == 0
    assert fee_info['status'] == 'On time'

def test_late_fee_under_7_days(monkeypatch):
    borrow_date = datetime.now() - timedelta(days=22)
    due_date = borrow_date + timedelta(days=14)
    monkeypatch.setattr('library_service.conn_execute_read', lambda q,p=(): [{"borrow_date": borrow_date.isoformat(), "due_date": due_date.isoformat(), "return_date": None}])
    fee_info = calculate_late_fee_for_book("000001", 1)
    assert fee_info['days_overdue'] == 8
    assert fee_info['fee_amount'] == 4.5  # 7*0.5 + 1*1.0

def test_late_fee_over_7_days(monkeypatch):
    borrow_date = datetime.now() - timedelta(days=30)
    due_date = borrow_date + timedelta(days=14)
    monkeypatch.setattr('library_service.conn_execute_read', lambda q,p=(): [{"borrow_date": borrow_date.isoformat(), "due_date": due_date.isoformat(), "return_date": None}])
    fee_info = calculate_late_fee_for_book("000001", 1)
    assert fee_info['fee_amount'] <= 15.0  # respects max cap

# ========================
# R6: Book Search
# ========================

def test_search_by_title():
    insert_book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 1, 1)
    results = search_books_in_catalog("Gatsby", "title")
    assert any("Gatsby" in book['title'] for book in results)

def test_search_by_author():
    insert_book("To Kill a Mockingbird", "Harper Lee", "9780061120084", 1, 1)
    results = search_books_in_catalog("Harper", "author")
    assert all("Harper" in book['author'] for book in results)

def test_search_by_isbn():
    insert_book("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 1, 1)
    results = search_books_in_catalog("9780743273565", "isbn")
    assert len(results) == 1
    assert results[0]['isbn'] == "9780743273565"

def test_search_invalid_type():
    results = search_books_in_catalog("anything", "invalid")
    assert results == []

# ========================
# R7: Patron Status Report
# ========================

def test_patron_status_valid():
    insert_book("Book 1", "Author", "9780000000004", 1, 1)
    borrow_book_by_patron("000001", 1)
    report = get_patron_status_report("000001")
    assert report['status'] == "success"
    assert report['currently_borrowed_count'] >= 1
    assert isinstance(report['currently_borrowed_books'], list)

def test_patron_status_invalid_id():
    report = get_patron_status_report("123")
    assert report['status'] == "Invalid patron ID"
