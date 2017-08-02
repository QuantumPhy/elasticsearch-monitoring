import httplib
import ssl
import logging
from socket import error
logger = logging.getLogger("NODE_FINDER")

CHOSEN_MASTERS = {}


def get_master(cluster, config):
    hosts = config["eshosts"].split(",")
    if cluster not in CHOSEN_MASTERS:
        master, conn = next(
            ((h, c) for host in hosts for r, h, c in Try(host, config) if r), (None, None)
        )
        if master and conn:
            CHOSEN_MASTERS[cluster] = {"host": master, "connection": conn}
        else:
            raise Exception("No valid master found for cluster {0}".format(cluster))
    return CHOSEN_MASTERS[cluster]


def Try(hostname, config):
    try:
        if config.get("secure", False):
            conn = httplib.HTTPSConnection(hostname, context=ssl._create_unverified_context())
            from base64 import b64encode
            credentials = b64encode(
                b"{0}:{1}".format(config.get("username", ""), config.get("password", ""))
            ).decode("ascii")
            headers = {'Authorization': 'Basic %s' % credentials}
        else:
            conn = httplib.HTTPConnection(hostname)
            headers = {}
        conn.request("GET", "/", headers=headers)
        conn.getresponse().read()
        return [(True, hostname, conn)]
    except error as e:
        logger.warn("Host %s throws %s", hostname, e)
        return [(False, None, None)]
