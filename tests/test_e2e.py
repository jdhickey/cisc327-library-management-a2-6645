import pytest
import time
from services.library_service import *
from database import *

def test_add_book_flow(page, live_server):
    page.goto(live_server + "/add_book")
    page.fill("input#title", "Test Book")
    page.fill("input#author", "Test Author")
    page.fill("input#isbn", "9781234567890")
    page.fill("input#total_copies", "3")

    page.click("text=Add Book to Catalog")
    page.wait_for_selector(".flash-success")
    assert "successfully" in page.text_content(".flash-success").lower()
    page.goto(live_server + "/catalog")
    assert page.locator("text=Test Book").count() > 0
