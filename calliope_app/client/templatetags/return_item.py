from django import template

register = template.Library()


def return_item(l, i):
    try:
        index = int(i)
    except ValueError:
        index = i
    try:
        return l[index]
    except Exception:
        return None


register.filter('return_item', return_item)
