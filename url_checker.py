from master import get_conn

try:
    import simplejson as json
except ImportError:
    import json

with open("urls.json") as f:
    urls_data = json.load(f)


def sort(x):
    return (x.get("success", False), x.get("url", ""))


def table(title, l):
    temp = """
        <table width='100%' border=1 cellpadding=3 cellspacing=0>
        <caption>{0}</caption>
        <tr><th>Expected</th><th>Actual</th><th>URL</th></tr>
    """.format(title)
    for item in sorted(l, key=sort):
        temp += "<tr><td>" + "</td><td>".join([
            str(item["expected"] or ""),
            str(item["actual"] or ""),
            str(item["url"] or "")
        ]) + "</td></tr>"
    return temp + "</table><br/>"


def url_checker():
    results = {
        "severity": "INFO",
        "title": "URLs Checker",
        "body": ""
    }
    responses = []
    for key, value in urls_data.items():
        res, _, conn = get_conn(value.get("host"), value)[0]
        expected = value.get("expectedHTTPCode", 200)
        url = "{0}://{1}{2}".format(
            value.get("protocol", "http"),
            value.get("host", ""),
            value.get("path", "")
        )
        result = {
            "success": True,
            "expected": expected,
            "url": url
        }
        if res:
            try:
                r1 = conn(value.get("path", ""))
                r1.read()
                result.update({
                    "success": int(r1.status) == expected,
                    "actual": r1.status
                })
            except Exception, ex:
                result.update({
                    "success": False,
                    "actual": str(ex)
                })
        else:
            result.update({
                "success": False,
                "actual": "Unable to establish connection to {0}".format(url)
            })
        responses.append(result)

    if any(not r.get("success", False) for r in responses):
        results["severity"] = "FATAL"
        results["body"] = table("URLs Checker", responses)

    return results
