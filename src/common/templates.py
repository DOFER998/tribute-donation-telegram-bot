from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils.formatting import calc_progress, format_amount

_TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'

_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(['html.j2']),
    enable_async=True,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=False,
)
cast('dict[str, Any]', _env.filters)['amount'] = format_amount
cast('dict[str, Any]', _env.globals)['progress'] = calc_progress


async def render(template_name: str, **context: object) -> str:
    template = _env.get_template(template_name)
    text = await template.render_async(**context)
    return text.strip()
