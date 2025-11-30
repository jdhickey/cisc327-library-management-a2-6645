Jack Hickey  
20336645  
(Group 2 - Qiru Jin)  

| Function Name                 | Implementation Status | What is missing                    |  
|-------------------------------|-----------------------|------------------------------------|
| R1: Add Book To Catalog       | Complete              | N/A                                |
| R2: Book Catalog Display      | Complete              | N/A                                |
| R3: Book Borrowing Interface  | Partial               | Accept book ID as a form parameter |
| R4: Book Return Processing    | Complete              | N/A                                |
| R5: Late Fee Calculation API  | Complete              | N/A                                |
| R6: Book Search Functionality | Complete              | N/A                                |
| R7: Patron Status Report      | Partial               | Dedicated page in the app          |

My experience completing the functional implementation was mostly straightforward. The main challenge
was learning how to interact correctly with the database layer, but after some tinkering
I became comfortable with it. The business logic itself was relatively direct to implement once the database
operations were working properly. As of now, although the functional implementation is complete, 
there is still some UI-related content  that needs to be completed.

Additional test cases:
3 test cases for R2
3 modifications for R5 tests, added 1 to test overdue
4 modifications for R6 tests
3 modifications for R7 tests