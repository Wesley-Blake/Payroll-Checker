from string import Template

from src import templates

PLAIN_TEMPLATES = [
    "NOT_STARTED_TEMPLATE",
    "INCORRECT_EARN_CODE_TEMPLATE",
    "OVERTIME_TEMPLATE",
    "OVER_TWELVE_TEMPLATE",
    "WEEKEND_OT_TEMPLATE",
    "UNION_WEEKEND_OT_TEMPLATE",
    "OVERLAPPING_TEMPLATE",
    "PENDING_TEMPLATE",
]

SUBSTITUTION_TEMPLATES = [
    "HOLIDAY_DATE_TEMPLATE",
    "HOLIDAY_TYPE_TEMPLATE",
]


def test_plain_templates_are_non_empty_strings():
    for name in PLAIN_TEMPLATES:
        value = getattr(templates, name)
        assert isinstance(value, str)
        assert value.strip()


def test_substitution_templates_accept_list_o_holidays():
    for name in SUBSTITUTION_TEMPLATES:
        template = getattr(templates, name)
        assert isinstance(template, Template)
        rendered = template.substitute(list_o_holidays="2026-01-01, 2026-07-04")
        assert "2026-01-01, 2026-07-04" in rendered
