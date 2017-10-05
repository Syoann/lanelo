from django import template
register = template.Library()


@register.filter
def join_by_attr(l, attr_name, separator=', '):
    return separator.join(str(getattr(elem, attr_name)) for elem in l)
