from tabularize_json import tabularize, json


def sort(item):
    return -float(item["disk.percent"] or 0), -int(item["disk.avail"] or 0), -int(item["disk.used"] or 0)


def table(title, l):
    temp = """
        <table width='100%' border=1 cellpadding=3 cellspacing=0>
        <caption>{0}</caption>
        <tr><th>Ratio</th><th>Total</th><th>Used</th><th>Available</th><th>Node</th><th>IP</th><th>Host</th><th>Shards</th></tr>
    """.format(title)
    for item in sorted(l, key=sort):
        temp += "<tr><td>" + "</td><td>".join([
            item["disk.percent"] or "",
            item["disk.total"] or "",
            item["disk.used"] or "",
            item["disk.avail"] or "",
            item["node"] or "",
            item["ip"] or "",
            item["host"] or "",
            item["shards"] or "",
        ]) + "</td></tr>"
    return temp + "</table><br/>"


def allocations(connection):
    r1 = connection("/_cat/allocation?bytes=m")
    response = r1.read()
    result = {
        "severity": "INFO",
        "title": "Allocations",
        "body": ""
    }
    if r1.status != 200:
        result = {
            "severity": "FATAL",
            "title": "Allocations check failed with HTTP Code [{0}]".format(r1.status),
            "body": tabularize(response)
        }
    else:
        allocs = json.loads(response)
        warn = [a for a in allocs if 80.0 < float(a["disk.percent"] or 0) < 85.0]
        errors = [a for a in allocs if float(a["disk.percent"] or 0) >= 85]
        unassigned = [a for a in allocs if a["node"] == "UNASSIGNED"]

        if errors:
            result["severity"] = "FATAL"
        elif warn or unassigned:
            result["severity"] = "WARNING"

        if unassigned:
            result["body"] += table("Unassigned Shards", unassigned)
        if errors:
            result["body"] += table("Allocations Maxed out", errors)
        if warn:
            result["body"] += table("Allocations Maxing out", warn)

    return result
