import pytest
from library_service import *
from database import *

@pytest.fixture
def fresh_db():
    conn = get_db_connection()
    conn.execute('''DROP TABLE books''')
    conn.execute('''DROP TABLE borrow_records''')
    conn.close()

    init_database()
    yield

def test_add_1(fresh_db):
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    assert success == True
    assert "successfully added" in message.lower()

def test_add_2(fresh_db):
    success, message = add_book_to_catalog("", "Test Author","1234567890124", 5)
    assert success == False
    assert "title is required" in message.lower()

def test_add_3(fresh_db):
    success, message = add_book_to_catalog("Testing Book", "", "1234567890125",5)
    assert success == False
    assert "author is required" in message.lower()

def test_add_4(fresh_db):
    success, message = add_book_to_catalog("Testing Book", "Testing Author", "0",5)
    assert success == False
    assert "isbn must" in message.lower()

def test_add_5(fresh_db):
    success, message = add_book_to_catalog("Testing a Book", "Testing A. Author","1234567890126", -1)
    assert success == False
    assert "total copies must" in message.lower()

def test_get_all_1(fresh_db):
    books = get_all_books()
    assert isinstance(books, list)
    if books:
        book = books[0]
        for key in ['id', 'title', 'author', 'isbn', 'available_copies', 'total_copies']:
            assert key in book

def test_get_all_2(fresh_db):
    books = get_all_books()
    if books:
        for b in books:
            assert isinstance(b['id'], int)
            assert b['title']
            assert b['author']
            assert len(b['isbn']) == 13 and isinstance(b['isbn'], str)
            assert 0 <= b['available_copies'] <= b['total_copies']

def test_get_all_3(fresh_db):
    add_book_to_catalog("New Book", "New Author", "1234567891111", 6)
    books = get_all_books('id')

    target = books[-1]
    book_id = target['id']
    initial_available = target['available_copies']

    borrow_book_by_patron("001122", book_id)
    updated = [b for b in get_all_books('id') if b['id'] == book_id][0]
    assert updated['available_copies'] <= initial_available

    return_book_by_patron("001122", book_id)
    final = [b for b in get_all_books('id') if b['id'] == book_id][0]
    assert final['available_copies'] == initial_available


def test_borrow_1(fresh_db):
    success, message = borrow_book_by_patron("000000", 1)
    assert success == True
    assert "successfully" in message.lower()

def test_borrow_2(fresh_db):
    success, message = borrow_book_by_patron("1", 1)
    assert success == False
    assert "invalid patron" in message.lower()

def test_borrow_3(fresh_db):
    success, message = borrow_book_by_patron("000000", 3)
    assert success == False
    assert "not available" in message.lower()

def test_borrow_4(fresh_db):
    success, message = borrow_book_by_patron("000000", 0)
    assert success == False
    assert "not available" in message.lower()

def test_return_1(fresh_db):
    success, message = return_book_by_patron("111", 4)
    assert success == False
    assert "invalid patron" in message.lower()

def test_return_2(fresh_db):
    success, message = return_book_by_patron("000000", 3)
    assert success == False
    assert "not borrowed" in message.lower()

def test_return_3(fresh_db):
    borrow_book_by_patron("000000", 1)
    success, message = return_book_by_patron("000000", 1)
    assert success == True
    assert "successfully" in message.lower()

def test_return_4(fresh_db):
    success, message = return_book_by_patron("000000", 304)
    assert success == False
    assert "book not" in message.lower()

def test_fees_1(fresh_db):
    """
    If patron ID is not 6 digits, the function should still return a dict,
    with fee_amount = 0 and status reflecting invalid patron.
    """
    result = calculate_late_fee_for_book("1280", 4)
    assert result['fee_amount'] == 0
    assert "invalid patron" in result['status'].lower()

def test_fees_2(fresh_db):
    """
    If book ID is not valid the function should still return a dict,
    with fee_amount = 0 and status reflecting invalid ID.
    """
    result = calculate_late_fee_for_book("000000", 304)
    assert result['fee_amount'] == 0
    assert "not found" in result['status'].lower()

def test_fees_3(fresh_db):
    """
    Since book is both borrowed and returned in these unit tests, it should
    not be overdue.
    """
    borrow_book_by_patron("000000", 1)

    result = calculate_late_fee_for_book("000000", 1)
    assert result['fee_amount'] == 0
    assert result['days_overdue'] == 0

    return_book_by_patron("000000", 1)

def test_fees_4(fresh_db):
    """
    This book is not available so should never be overdue.
    """
    result = calculate_late_fee_for_book("000000", 3)
    assert result['fee_amount'] == 0
    assert result['days_overdue'] == 0
    assert "no corresponding borrow record" in result['status'].lower()
    assert isinstance(result, dict)

def test_fees_5(monkeypatch, fresh_db):
    """
    Testing an overdue book
    """

    from datetime import datetime, timedelta
    days_overdue = 10

    now = datetime.now()
    due_date_iso = (now - timedelta(days=days_overdue)).isoformat()
    borrow_date_iso = (now - timedelta(days=(days_overdue + 14))).isoformat()

    mock_record = {"patron_id": "000000", "book_id": 4, "borrow_date": borrow_date_iso, "due_date": due_date_iso, "return_date": None}

    monkeypatch.setattr('database.conn_execute_read', lambda q, p=(): mock_record)
    result = calculate_late_fee_for_book("000000", 4)
    expected_fee = round((7 * 0.50) + (days_overdue - 7) * 1.00, 2)

    assert result['days_overdue'] == days_overdue
    assert result['fee_amount'] == expected_fee
    assert result['status'].lower() == "overdue"



def test_search_1(fresh_db):
    result = search_books_in_catalog("1984", "title")
    assert all(isinstance(book, dict) for book in result)
    assert all("1984" in book['title'] for book in result)
    assert isinstance(result, list)

def test_search_2(fresh_db):
    result = search_books_in_catalog("George", "author")
    assert isinstance(result, list)

def test_search_3(fresh_db):
    result = search_books_in_catalog("9780451524935", "isbn")
    assert len(result) == 1
    assert result[0]['isbn'] == "9780451524935"
    assert isinstance(result, list)

def test_search_4(fresh_db):
    result = search_books_in_catalog("0p", "title")
    assert isinstance(result, list)
    assert result == []

def test_patron_1(fresh_db):
    expected_keys = [
        "status",
        "patron_id",
        "currently_borrowed_count",
        "currently_borrowed_books",
        "total_late_fees",
        "borrowing_history"
    ]

    result = get_patron_status_report("0")
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in result

def test_patron_2(fresh_db):
    result = get_patron_status_report("000111")
    assert isinstance(result, dict)

def test_patron_3(fresh_db):
    result = get_patron_status_report("000000")
    assert result['patron_id'] == "000000"
    assert isinstance(result, dict)

def test_patron_4(fresh_db):
    result = get_patron_status_report("gol")
    assert isinstance(result, dict)
    assert "invalid patron" in result['status']