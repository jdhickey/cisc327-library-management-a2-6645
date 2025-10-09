Jack Hickey  
20336645  
(Group 2 - Qiru Jin)  

| Function Name                 | Implementation Status | What is missing                                                                          |  
|-------------------------------|-----------------------|------------------------------------------------------------------------------------------|
| R1: Add Book To Catalog       | Complete              | N/A                                                                                      |
| R2: Book Catalog Display      | Complete              | N/A                                                                                      |
| R3: Book Borrowing Interface  | Partial               | Accept book ID as a form parameter                                                       |
| R4: Book Return Processing    | Partial               | Verify patron borrowed book, update copy count and record return date, display late fees |
| R5: Late Fee Calculation API  | Partial               | Unimplemented                                                                            |
| R6: Book Search Functionality | Partial               | Functionality to execute search                                                          |
| R7: Patron Status Report      | Partial               | Dedicated page in the app, functionality to produce report                               |

============================= test session starts ==============================
collecting ... collected 25 items

test_all.py::test_add_1 PASSED                                           [  4%]
test_all.py::test_add_2 PASSED                                           [  8%]
test_all.py::test_add_3 PASSED                                           [ 12%]
test_all.py::test_add_4 PASSED                                           [ 16%]
test_all.py::test_add_5 PASSED                                           [ 20%]
test_all.py::test_borrow_1 PASSED                                        [ 24%]
test_all.py::test_borrow_2 PASSED                                        [ 28%]
test_all.py::test_borrow_3 PASSED                                        [ 32%]
test_all.py::test_borrow_4 PASSED                                        [ 36%]
test_all.py::test_return_1 FAILED                                        [ 40%]
>       assert "invalid patron" in message.lower()
test_all.py:52: AssertionError

test_all.py::test_return_2 FAILED                                        [ 44%]
>       assert "not borrowed" in message.lower()
test_all.py:57: AssertionError

test_all.py::test_return_3 FAILED                                        [ 48%]
>       assert success == True
test_all.py:61: AssertionError

test_all.py::test_return_4 FAILED                                        [ 52%]
'book not' != 'book return functionality is not yet implemented.'
>       assert "book not" in message.lower()
test_all.py:67: AssertionError

test_all.py::test_fees_1 FAILED                                          [ 56%]
>       assert result['fee_amount'] == 0
test_all.py:75: TypeError

test_all.py::test_fees_2 FAILED                                          [ 60%]
>       assert result['fee_amount'] == 0
test_all.py:83: TypeError

test_all.py::test_fees_3 FAILED                                          [ 64%]
>       assert result['fee_amount'] == 0
test_all.py:91: TypeError

test_all.py::test_fees_4 FAILED                                          [ 68%]
>       assert result['fee_amount'] == 0
test_all.py:99: TypeError

test_all.py::test_search_1 PASSED                                        [ 72%]
test_all.py::test_search_2 PASSED                                        [ 76%]
test_all.py::test_search_3 PASSED                                        [ 80%]
test_all.py::test_search_4 PASSED                                        [ 84%]
test_all.py::test_patron_1 PASSED                                        [ 88%]
test_all.py::test_patron_2 PASSED                                        [ 92%]
test_all.py::test_patron_3 PASSED                                        [ 96%]
test_all.py::test_patron_4 PASSED                                        [100%]

========================= 8 failed, 17 passed in 0.05s =========================

I designed these unit tests assuming I was evaluating the functions after they have been implemented.
That's why so many of them fail, because those functionalities aren't implemented yet.