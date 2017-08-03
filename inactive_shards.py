import logging
from tabularize_json import tabularize
logger = logging.getLogger("SHARDS")

try:
    import simplejson as json
except ImportError:
    import json


def sort(item):
    return (item["index"], int(item["shard"]), item["prirep"], item["node"])


def table(title, l):
    temp = """
        <table width='100%' border=1 cellpadding=3 cellspacing=0>
        <caption>{0} Shards</caption>
        <tr><th>Index</th><th>Shard</th><th>prirep</th><th>Reason</th><th>Docs</th><th>Store</th><th>IP</th><th>Node</th></tr>
    """.format(title)
    for item in sorted(l, key=sort):
        temp += "<tr><td>" + "</td><td>".join([
            item["index"],
            item["shard"],
            item["prirep"],
            item["unassigned.reason"] or "",
            item["docs"] or '0',
            item["store"] or '0',
            item["ip"] or "",
            item["node"] or ""
        ]) + "</td></tr>"
    return temp + "</table><br/>"


def inactive_shards(cluster, connection):
    r1 = connection("/_cat/shards?h=index,shard,prirep,state,unassigned.reason,docs,store,ip,node")
    response = r1.read()
    result = {
        "severity": "INFO",
        "title": "Shards",
        "body": ""
    }
    if r1.status != 200:
        result = {
            "severity": "FATAL",
            "title": "Shards Check Failed with HTTP Code [{0}]".format(r1.status),
            "body": tabularize(response)
        }
    else:
        shards_data = json.loads(response)
        started = [shard for shard in shards_data if shard["state"] == "STARTED"]
        init = [shard for shard in shards_data if shard["state"] == "INITIALIZING"]
        relocating = [shard for shard in shards_data if shard["state"] == "RELOCATING"]
        unassigned = [shard for shard in shards_data if shard["state"] == "UNASSIGNED"]

        if init or any(s["prirep"] == "p" for s in relocating):
            result["severity"] = "FATAL"
        elif unassigned and all(u["unassigned.reason"] == "INDEX_CREATED" for u in unassigned):
            result["severity"] = "WARNING"
        elif unassigned:
            result["severity"] = "FATAL"

        result["body"] += """<table width='100%' border=1 cellpadding=3 cellspacing=0>
            <tr><td>Total</td><td>{0}</td></tr>
            <tr><td>Started</td><td>{1}</td></tr>
            <tr><td>Initializing</td><td>{2}</td></tr>
            <tr><td>Relocating</td><td>{3}</td></tr>
            <tr><td>Unassigned</td><td>{4}</td></tr>
        </table><br />""".format(
            len(shards_data),
            len(started),
            len(init),
            len(relocating),
            len(unassigned)
        )

        if unassigned:
            result["body"] += table("Unassigned", unassigned)
        if init:
            result["body"] += table("Initializing", init)
        if relocating:
            result["body"] += table("Relocating", init)
    return result
