from tabularize_json import tabularize, json


def sort(item):
    return (item["name"] or "", item["host"] or "", item["ip"] or "")


def get_master_mark(data):
    return "N" if data == "-" else "Y" if data == "m" else "*"


def table(title, l, nodes):
    temp = """
        <table width='100%' border=1 cellpadding=3 cellspacing=0>
        <caption>{0}</caption>
        <tr><th>Node's Name</th><th>Node's Hostname</th><th>Node's IP</th><th>Master?</th></tr>
    """.format(title)
    for item in sorted((nodes[item] for item in l), key=sort):
        temp += "<tr><td>" + "</td><td>".join([
            item["name"] or "",
            item["host"] or "",
            item["ip"] or "",
            get_master_mark(item["master"] or "")
        ]) + "</td></tr>"
    return temp + "</table><br/>"


def nodes(cluster, connection):
    r1 = connection("/_cat/nodes?bytes=m")
    response = r1.read()
    result = {
        "severity": "INFO",
        "title": "Nodes",
        "body": ""
    }
    if r1.status != 200:
        result = {
            "severity": "FATAL",
            "title": "Nodes check failed with HTTP Code [{0}]".format(r1.status),
            "body": tabularize(response)
        }
    else:
        new_nodes = dict()
        for node in json.loads(response):
            new_nodes[node["name"]] = node
        try:
            old_nodes = dict()
            with open("{0}_nodes.txt".format(cluster), "r") as f:
                for line in f:
                    a = line.strip().split("\t")
                    old_nodes[a[0]] = {
                        "name": a[0],
                        "host": a[1],
                        "ip": a[2],
                        "master": a[3]
                    }
        except IOError:
            pass

        new_node_names = set(new_nodes)
        old_node_names = set(old_nodes)
        missing_node_names = old_node_names - new_node_names
        fresh_node_names = new_node_names - old_node_names

        if missing_node_names:
            result["severity"] = "FATAL"
        elif fresh_node_names:
            result["severity"] = "WARNING"

        old_and_new_nodes = old_nodes.copy()
        old_and_new_nodes.update(new_nodes)

        if missing_node_names:
            result["body"] += table("Missing nodes",
                                    missing_node_names, old_and_new_nodes)
        if fresh_node_names:
            result["body"] += table("New Nodes joined the cluster",
                                    fresh_node_names, old_and_new_nodes)

        if missing_node_names or fresh_node_names:
            with open("{0}_nodes.txt".format(cluster), "w") as f:
                f.write(
                    "\n".join(
                        "\t".join(
                            (
                                item["name"],
                                item["host"],
                                item["ip"],
                                get_master_mark(item["master"] or "")
                            )
                        ) for item in new_nodes.values()
                    )
                )

    return result
