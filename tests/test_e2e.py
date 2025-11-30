
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

def test_borrow_book_flow(page, live_server):
    page.goto(live_server + "/add_book")
    page.fill("input#title", "Borrow-Book")
    page.fill("input#author", "Flow")
    page.fill("input#isbn", "9781111111111")
    page.fill("input#total_copies", "2")
    page.click("text=Add Book to Catalog")
    page.wait_for_selector(".flash-success")

    page.goto(live_server + "/catalog")
    page.wait_for_selector("table")
    row = page.locator("tr", has_text="Borrow-Book")
    assert row.count() == 1

    row.locator("input[name='patron_id']").fill("000000")
    row.locator("button.btn-success").click()

    page.wait_for_selector(".flash-success")
    msg = page.text_content(".flash-success").lower()
    assert "borrow" in msg or "success" in msg