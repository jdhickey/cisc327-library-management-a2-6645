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
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 5.0, 'days_overdue': 3, 'status': 'Overdue'})
    mocker.patch('services.library_service.get_book_by_id', return_value=sample_book)

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
        description=f"Late fees for '{sample_book['title']}'"
    )

def test_pay_late_fees_2(fresh_db, mocker, sample_book):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 7.5, 'days_overdue': 5, 'status': 'Overdue'})
    mocker.patch('services.library_service.get_book_by_id', return_value=sample_book)

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, "", "declined")

    success, message, txn = pay_late_fees("111111", 1, payment_gateway=mock_gateway)

    assert success == False
    assert "declined" in message.lower()
    assert txn is None
    mock_gateway.process_payment.assert_called_once()

def test_pay_late_fees_3(fresh_db, mocker, sample_book):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 10.0, 'days_overdue': 6, 'status': 'Overdue'})
    mocker.patch('services.library_service.get_book_by_id', return_value=sample_book)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("-1", 1, payment_gateway=mock_gateway)

    assert success == False
    assert "invalid" in message.lower()
    assert txn is None
    mock_gateway.assert_not_called()

def test_pay_late_fees_4(fresh_db, mocker, sample_book):
    mocker.patch('services.library_service.calculate_late_fee_for_book', return_value={'fee_amount': 0.0, 'days_overdue': 0, 'status': 'On time'})
    mocker.patch('services.library_service.get_book_by_id', return_value=sample_book)
    mock_gateway = Mock(spec=PaymentGateway)

    success, message, txn = pay_late_fees("111111", 1, payment_gateway=mock_gateway)
    assert success == False
    assert "no late fees" in message.lower()
    assert txn is None
    mock_gateway.assert_not_called()

def test_refund_late_fee_1(fresh_db, mocker):
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund OK")

    success, message = refund_late_fee_payment("txn_0000", 5.0, payment_gateway=mock_gateway)

    assert success == True
    assert "refund" in message.lower()
    mock_gateway.refund_payment.assert_called_once_with("txn_0000", 5.0)

def test_refund_late_fee_2(fresh_db, mocker):
    mock_gateway = Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("BAD", 5.0, payment_gateway=mock_gateway)

    assert success == False
    assert "invalid" in message.lower()
    mock_gateway.refund_payment.assert_not_called()

def test_refund_late_fee_3(fresh_db, mocker):
    mock_gateway = Mock(spec=PaymentGateway)
    success, message = refund_late_fee_payment("txn_0000", -5.0, payment_gateway=mock_gateway)

    assert success == False
    assert "greater" in message.lower()
    mock_gateway.refund_payment.assert_not_called()

def test_refund_late_fee_4(fresh_db, mocker):
    mock_gateway = Mock(spec=PaymentGateway)
    success, message = refund_late_fee_payment("txn_0000", 16.0, payment_gateway=mock_gateway)

    assert success == False
    assert "exceeds" in message.lower()
    mock_gateway.refund_payment.assert_not_called()

def test_refund_late_fee_5(fresh_db, mocker):
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("Gateway timeout")

    success, message = refund_late_fee_payment("txn_9999", 5.0, payment_gateway=mock_gateway)

    assert success == False
    assert "processing error" in message.lower()
    mock_gateway.refund_payment.assert_called_once_with("txn_9999", 5.0)
