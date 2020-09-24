from django import template
register = template.Library()


@register.filter
def join_by_attr(l, attr_name, separator=', '):
    return separator.join(str(getattr(elem, attr_name)) for elem in l)


@register.filter
def diff(value, arg):
    return len(value) - len(arg)

@register.filter
def lmax(l):
    return max(l)

@register.filter
def lmin(l):
    print(min(l))
    return min(l)
