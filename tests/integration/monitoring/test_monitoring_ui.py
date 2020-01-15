def test_ui_index_page_is_available(ui):
    response = ui.get("/")
    assert response.status_code == 200


def test_ui_full_index_page_is_available(ui):
    response = ui.get("/?mode=full")
    assert response.status_code == 200


def test_ui_simple_report_page_is_available(ui):
    response = ui.get("/report/08a914cde0")
    assert response.status_code == 200


def test_ui_complex_report_page_is_available(ui):
    response = ui.get("/report/c032adc1ff")
    assert response.status_code == 200


def test_ui_invalid_report_page_is_unavailable(ui):
    response = ui.get("/report/blah")
    assert response.status_code == 404


def test_void_ui_index_page_is_available(void_ui):
    response = void_ui.get("/")
    assert response.status_code == 200
