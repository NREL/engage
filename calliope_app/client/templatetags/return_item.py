from django import template

register = template.Library()


def return_item(l, i):
    try:
        return l[i]
    except Exception:
        try:
            return l[int(i)]
        except Exception:
            return None

register.filter('return_item', return_item)

def return_first_key(l):
    if l and isinstance(l, dict):
        return list(l.keys())[0]
    return None

register.filter('return_first_key', return_first_key)

def find_param_dup_tag(mvalues, index):
    if mvalues and index:
        return [m['dup_tag'] for m in mvalues if index == m['index']][0]
    return None

register.filter('find_param_dup_tag', find_param_dup_tag)
