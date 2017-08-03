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
            ((h, c) for host in hosts for r, h, c in get_conn(host, config) if r), (None, None)
        )
        if master and conn:
            CHOSEN_MASTERS[cluster] = {"host": master, "connection": conn}
        else:
            raise StandardError("No valid master found for cluster {0}".format(cluster))
    return CHOSEN_MASTERS[cluster]


def request(connection, headers):
    def get(path):
        connection.request("GET", path, headers=headers)
        return connection.getresponse()
    return get


def get_conn(hostname, config):
    try:
        headers = {'Content-Type': 'application/json'}
        if config.get("secure", False):
            import sys
            if sys.version_info >= (2, 7, 9):
                conn = httplib.HTTPSConnection(hostname, context=ssl._create_unverified_context())
            else:
                conn = httplib.HTTPSConnection(hostname)
            from base64 import b64encode
            credentials = b64encode(
                b"{0}:{1}".format(config.get("username", ""), config.get("password", ""))
            ).decode("ascii")
            headers['Authorization'] = 'Basic %s' % credentials
        else:
            conn = httplib.HTTPConnection(hostname)
        conn.request("GET", "/", headers=headers)
        conn.getresponse().read()
        return [(True, hostname, request(conn, headers))]
    except error as e:
        logger.warn("Host %s throws %s", hostname, e)
        return [(False, None, None)]
    except Exception as e:
        logger.warn("Unexpected Exception %s with %s", e, hostname)
        return [(False, None, None)]
