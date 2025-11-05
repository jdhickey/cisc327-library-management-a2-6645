from unittest.mock import Mock

import pytest
from services.library_service import *
from database import *

@pytest.fixture
def fresh_db():
    conn = get_db_connection()
    conn.execute('''DROP TABLE books''')
    conn.execute('''DROP TABLE borrow_records''')
    conn.close()

    init_database()
    add_sample_data()
    yield

@pytest.fixture
def sample_book():
    return {'id': 10, 'title': 'Test Book', 'author': 'Mr. Name', 'isbn': '1234567890987'}

def test_pay_late_fees_1(fresh_db, mocker, sample_book):
    mocker.patch('services.library_services.calculate_late_fees_for_book', return_value={'fee_amount': 5.0, 'days_overdue': 3, 'status': 'Overdue'})
    mocker.patch('services.library_services.get_book_by_id', return_value=sample_book)

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_0000", "test")

    success, message, txn = pay_late_fees("111111", 1, payment_gateway=mock_gateway)
    assert success == True
    assert "success" in message.lower()
    assert txn == "txn_0000"
    mock_gateway.process_payment.assert_called_once()
    mock_gateway.process_payment.assert_called_with(
        patron_id="111111",
        amount=5.0,
    )

def test_pay_late_fees_2(fresh_db, mocker, sample_book):
    mocker.patch('services.library_services.calculate_late_fees_for_book', return_value={'fee_amount': 7.5, 'days_overdue': 5, 'status': 'Overdue'})
    mocker.patch('services.library_services.get_book_by_id', return_value=sample_book)

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, "", "declined")

    success, message, txn = pay_late_fees("111111", 1, payment_gateway=mock_gateway)

    assert success == False
    assert "declined" in message.lower()
    assert txn is None
    mock_gateway.process_payment.assert_called_once()

def test_pay_late_fees_3(fresh_db, mocker, sample_book):
    mocker.patch('services.library_services.calculate_late_fees_for_book', return_value={'fee_amount': 10.0, 'days_overdue': 6, 'status': 'Overdue'})
    mocker.patch('services.library_services.get_book_by_id', return_value=sample_book)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("-1", 1, payment_gateway=mock_gateway)

    assert success == False
    assert "invalid" in message.lower()
    assert txn is None
    mock_gateway.assert_not_called()

def test_pay_late_fees_4(fresh_db, mocker, sample_book):
    mocker.patch('services.library_services.calculate_late_fees_for_book', return_value={'fee_amount': 0.0, 'days_overdue': 0, 'status': 'On time'})
    mocker.patch('services.library_services.get_book_by_id', return_value=sample_book)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("111111", 1, payment_gateway=mock_gateway)
    assert success == False
    assert "invalid" in message.lower()
    assert txn is None
    mock_gateway.assert_called_once()
