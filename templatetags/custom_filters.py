
import re
import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def quill_delta_to_html(value):
    try:
        # Handle both string JSON and FieldQuill objects
        delta_str = value if isinstance(value, str) else value.json
        delta = json.loads(delta_str)
        
        html = []
        for op in delta.get('ops', []):
            if 'insert' in op:
                text = op['insert']
                # ... rest of your existing conversion logic ...
        return mark_safe(''.join(html))
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        return f"Error rendering content: {str(e)}"


@register.filter
def to_range(value):
    """Converts a number into a range (used for iterating in templates)."""
    try:
        return range(int(value))
    except ValueError:
        return []


@register.filter
def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0  # Return a default value if conversion fails


@register.filter(name='add_class')
def add_class(value, arg):
    """
    Adds a CSS class to a form field.
    Usage: {{ form.field|add_class:"form-control" }}
    """
    return value.as_widget(attrs={"class": arg})


@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder_text):
    """Add a placeholder attribute to form fields."""
    field.field.widget.attrs.update({"placeholder": placeholder_text})
    return field


@register.filter
def split(value, delimiter="\n"):
    """
    Splits the input string by the given delimiter and returns a list.
    Default delimiter is a newline.
    """
    return value.split(delimiter)


@register.filter
def splits(value, arg):
    return value.split(arg)

@register.filter
def extract_links(value):
    if not isinstance(value, str):
        return ''
    links = re.findall(r'(https?://\S+)', value)
    return ', '.join(links)

@register.filter
def get_attribute(obj, attr_name):
    """Get attribute from object or dict"""
    if isinstance(obj, dict):
        return obj.get(attr_name)
    return getattr(obj, attr_name, None)



@register.simple_tag(takes_context=True)
def lookup_var(context, var_name):
    return context.get(var_name, 0)  # Return 0 if not found