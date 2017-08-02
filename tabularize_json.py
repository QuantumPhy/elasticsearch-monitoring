try:
    import simplejson as json
except ImportError:
    import json


def tabularize(data):
    result = "<table width='100%' border=1 cellpadding=3 cellspacing=0>"
    d = data if isinstance(data, dict) else json.loads(data)
    for key, value in d.iteritems():
        if isinstance(value, dict):
            v = tabularize(value)
            result += "<tr><td>{0}</td><td>{1}</td></tr>".format(key, v)
        elif isinstance(value, list):
            v = "<br />".join(map(tabularize, value))
            result += "<tr><td>{0}</td><td>{1}</td></tr>".format(key, v)
        else:
            result += "<tr><td>{0}</td><td>{1}</td></tr>".format(key, value)
    return result + "</table>"
