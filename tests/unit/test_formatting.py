from src.common import calc_progress, format_amount


def test_format_amount_integer():
    assert format_amount(100000) == '1 000'


def test_format_amount_thousand_separator():
    assert format_amount(69800000) == '698 000'


def test_format_amount_fractional():
    assert format_amount(100050) == '1 000.5'


def test_calc_progress_zero():
    p, bar = calc_progress(0, 1000)
    assert p == 0
    assert '▱' * 10 in bar


def test_calc_progress_full():
    p, bar = calc_progress(1000, 1000)
    assert p == 100
    assert '▰' * 10 in bar


def test_calc_progress_overflow():
    p, _ = calc_progress(2000, 1000)
    assert p == 100


def test_calc_progress_zero_target():
    p, _ = calc_progress(50, 0)
    assert p == 0
