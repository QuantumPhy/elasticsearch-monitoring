from tabularize_json import tabularize, json
import re


def sort(item):
    return item["s"], item["i"], item["h"]


def table(title, l):
    temp = """
        <table width='100%' border=1 cellpadding=3 cellspacing=0>
        <caption>{0} Indices</caption>
        <tr>
          <th>Health</th><th>Index</th><th>State</th><th>Primary</th><th>Replica</th><th>Size</th><th>Primary Size</th>
        </tr>
    """.format(title)
    for item in sorted(l, key=sort):
        temp += "<tr><td>" + "</td><td>".join([
            item["h"] or "",
            item["i"] or "",
            item["s"] or "",
            item["pri"] or "",
            item["rep"] or "",
            item["store.size"] or "",
            item["pri.store.size"] or "",
        ]) + "</td></tr>"
    return temp + "</table><br/>"


def is_white_listed(whitelisted):
    def temp(index):
        return any(j.search(index) is not None for j in whitelisted)
    return temp


def indices(connection, config):
    r1 = connection("/_cat/indices?bytes=m&h=i,h,s,pri,rep,store.size,pri.store.size")
    response = r1.read()
    result = {
        "severity": "INFO",
        "title": "Indices",
        "body": ""
    }
    if r1.status != 200:
        result = {
            "severity": "FATAL",
            "title": "Indices Check Failed with HTTP Code [{0}]".format(r1.status),
            "body": tabularize(response)
        }
    else:
        indices_data = json.loads(response)
        cfg_whitelisted_indices = config.get("whitelisted_indices", [])
        whitelisted_indices = set(map(lambda x: re.compile(x), cfg_whitelisted_indices))
        is_index_whitelisted = is_white_listed(whitelisted_indices)

        red = [i for i in indices_data if i["h"] == "red"]
        yellow = [i for i in indices_data if i["h"] == "yellow"]
        closed = [i for i in indices_data if i["s"] == "close"]
        opened = [i for i in indices_data if i["s"] == "open"]

        if red and not all(is_index_whitelisted(i["i"]) for i in red):
            result["severity"] = "FATAL"
        elif yellow and not all(is_index_whitelisted(i["i"]) for i in yellow):
            result["severity"] = "WARNING"
        elif closed and not all(is_index_whitelisted(i["i"]) for i in closed):
            result["severity"] = "WARNING"

        result["body"] += """<table width='100%' border=1 cellpadding=3 cellspacing=0>
            <tr><td>Total</td><td>{0}</td></tr>
            <tr><td>Red</td><td>{1}</td></tr>
            <tr><td>Yellow</td><td>{2}</td></tr>
            <tr><td>Green</td><td>{3}</td></tr>
            <tr><td>Open</td><td>{4}</td></tr>
            <tr><td>Closed</td><td>{5}</td></tr>
        </table><br />""".format(
            len(indices_data),
            len(red),
            len(yellow),
            len(indices_data) - len(red) - len(yellow) - len(closed),
            len(opened),
            len(closed)
        )

        if red:
            result["body"] += table("Red", red)
        if yellow:
            result["body"] += table("Yellow", yellow)
        if closed:
            result["body"] += table("Closed", closed)

    return result
