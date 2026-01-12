# reports/templatetags/reports_extras.py

from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another.
    Usage: {{ value|replace:"old_string,new_string" }}
    """
    # Unpack the arguments
    old, new = arg.split(',')
    return value.replace(old, new)