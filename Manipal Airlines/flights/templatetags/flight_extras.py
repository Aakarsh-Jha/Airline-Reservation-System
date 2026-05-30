from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def indian_currency(value):
    """Format number as Indian currency."""
    try:
        value = float(value)
        return f"₹{value:,.2f}"
    except (ValueError, TypeError):
        return value
