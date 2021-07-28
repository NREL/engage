from django import template

register = template.Library()


def add_commas(item):
    try:
        length = 0
        dec = str(item).split('.')
        if len(dec) > 1:
            length = len(dec[1])
        elif 'e-' in item:
            length = item.split('e-')[1]
        frmt = "{:,." + str(length) + "f}"
        pretty_string = frmt.format(float(item))
        return pretty_string
    except Exception:
        return item


register.filter('add_commas', add_commas)
