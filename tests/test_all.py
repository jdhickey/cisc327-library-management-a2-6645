import pytest
from library_service import *

def test_add_1():
    success, message = add_book_to_catalog("Test Book", "Test Author", "1234567890123", 5)
    assert success == True
    assert "successfully added" in message.lower()

def test_add_2():
    success, message = add_book_to_catalog("", "Test Author","1234567890124", 5)
    assert success == False
    assert "title is required" in message.lower()

def test_add_3():
    success, message = add_book_to_catalog("Testing Book", "", "1234567890125",5)
    assert success == False
    assert "author is required" in message.lower()

def test_add_4():
    success, message = add_book_to_catalog("Testing Book", "Testing Author", "0",5)
    assert success == False
    assert "isbn must" in message.lower()

def test_add_5():
    success, message = add_book_to_catalog("Testing a Book", "Testing A. Author","1234567890126", -1)
    assert success == False
    assert "total copies must" in message.lower()

def test_borrow_1():
    success, message = borrow_book_by_patron("000000", 4)
    assert success == True
    assert "successfully" in message.lower()

def test_borrow_2():
    success, message = borrow_book_by_patron("1", 1)
    assert success == False
    assert "invalid patron" in message.lower()

def test_borrow_3():
    success, message = borrow_book_by_patron("000000", 3)
    assert success == False
    assert "not available" in message.lower()

def test_borrow_4():
    success, message = borrow_book_by_patron("000000", 0)
    assert success == False
    assert "not found" in message.lower()

def test_return_1():
    success, message = return_book_by_patron("111", 4)
    assert success == False
    assert "invalid patron" in message.lower()

def test_return_2():
    success, message = return_book_by_patron("000000", 3)
    assert success == False
    assert "not borrowed" in message.lower()

def test_return_3():
    success, message = return_book_by_patron("000000", 4)
    assert success == True
    assert "successfully" in message.lower()

def test_return_4():
    success, message = return_book_by_patron("000000", 304)
    assert success == False
    assert "book not" in message.lower()

def test_fees_1():
    """
    If patron ID is not 6 digits, the function should still return a dict,
    with fee_amount = 0 and status reflecting invalid patron.
    """
    result = calculate_late_fee_for_book("1280", 4)
    assert result['fee_amount'] == 0

def test_fees_2():
    """
    If book ID is not valid the function should still return a dict,
    with fee_amount = 0 and status reflecting invalid ID.
    """
    result = calculate_late_fee_for_book("000000", 304)
    assert result['fee_amount'] == 0

def test_fees_3():
    """
    Since book is both borrowed and returned in these unit tests, it should
    not be overdue.
    """
    result = calculate_late_fee_for_book("000000", 4)
    assert result['fee_amount'] == 0
    assert result['days_overdue'] == 0

def test_fees_4():
    """
    This book is not available so should never be overdue.
    """
    result = calculate_late_fee_for_book("000000", 3)
    assert result['fee_amount'] == 0
    assert result['days_overdue'] == 0
    assert 'status' in result
    assert isinstance(result, dict)

def test_search_1():
    result = search_books_in_catalog("1984", "Title (partial match)")
    assert all(isinstance(book, dict) for book in result)
    assert isinstance(result, list)

def test_search_2():
    result = search_books_in_catalog("George", "Author (partial match)")
    assert isinstance(result, list)

def test_search_3():
    result = search_books_in_catalog("9780451524935", "ISBN (exact match)")
    assert isinstance(result, list)

def test_search_4():
    result = search_books_in_catalog("0p", "Title (partial match)")
    assert isinstance(result, list)

def test_patron_1():
    result = get_patron_status_report("0")
    assert isinstance(result, dict)

def test_patron_2():
    result = get_patron_status_report("000111")
    assert isinstance(result, dict)

def test_patron_3():
    result = get_patron_status_report("000000")
    assert isinstance(result, dict)

def test_patron_4():
    result = get_patron_status_report("gol")
    assert isinstance(result, dict)