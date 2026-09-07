from app.services.salary_parser import parse_salary


def test_kes_salary_range_recognized():
    low, high, currency, reliable = parse_salary("KSh 120,000 - 180,000")
    assert currency == "KES"
    assert reliable is True
    assert low == 120000.0 and high == 180000.0


def test_naira_symbol_recognized():
    low, high, currency, reliable = parse_salary("₦300,000 - 450,000")
    assert currency == "NGN"
    assert reliable is True


def test_naira_word_recognized():
    low, high, currency, reliable = parse_salary("200000 - 350000 Naira")
    assert currency == "NGN"
    assert reliable is True


def test_usd_recognized():
    low, high, currency, reliable = parse_salary("$1,500 - $2,500")
    assert currency == "USD"
    assert reliable is True


def test_unrecognized_currency_marked_unreliable():
    low, high, currency, reliable = parse_salary("Competitive salary")
    assert reliable is False
    assert low is None and high is None


def test_empty_salary_returns_unreliable_none():
    low, high, currency, reliable = parse_salary("")
    assert low is None and high is None and reliable is False


def test_k_suffix_shorthand():
    low, high, currency, reliable = parse_salary("KES 50k - 80k")
    assert low == 50000.0 and high == 80000.0
    assert currency == "KES"
