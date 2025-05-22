from django import template

register = template.Library()


def update_units_in(str, carrier):
    """
    Update the units in a string based on the carrier.
    """
    return str.replace("[[in_rate]]", carrier['rate']).replace("[[in_quantity]]", carrier['quantity'])

register.filter('update_units_in', update_units_in)

def update_units_out(str, carrier):
    """
    Update the units in a string based on the carrier.
    """
    return str.replace("[[out_rate]]", carrier['rate']).replace("[[out_quantity]]", carrier['quantity'])

register.filter('update_units_out', update_units_out)
