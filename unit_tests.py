import pytest
from library_service import (
    add_book_to_catalog
)

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