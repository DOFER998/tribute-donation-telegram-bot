from html import escape


def format_amount(kopecks: int) -> str:
    """копейки -> '1 234' / '1 234.56'"""
    rubles = kopecks / 100
    if rubles == int(rubles):
        return f'{int(rubles):,}'.replace(',', ' ')
    return f'{rubles:,.2f}'.replace(',', ' ').rstrip('0').rstrip('.')


def calc_progress(current: int, target: int, bar_length: int = 10) -> tuple[int, str]:
    percent = min(int(current * 100 / target), 100) if target > 0 else 0
    filled = int(bar_length * percent / 100)
    empty = bar_length - filled
    bar = '⟨' + '▰' * filled + '▱' * empty + '⟩'
    return percent, bar


def escape_html(text: str) -> str:
    return escape(text, quote=False)
