# myapp/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, arg):
    old, new = arg.split(',')
    result = value.replace(old, new)
    return result.strip()
