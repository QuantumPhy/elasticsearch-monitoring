import logging
from tabularize_json import tabularize
logger = logging.getLogger("HEALTH")

try:
    import simplejson as json
except ImportError:
    import json


def health(cluster, con):
    r1 = con("/_cat/health")
    response = r1.read()
    if r1.status != 200:
        return {
            "severity": "FATAL",
            "title": "Health Check Failed",
            "body": tabularize(response)
        }
    else:
        health_data = json.loads(response)[0]
        if health_data["status"] == "yellow":
            return {
                "title": "Health is Yellow",
                "severity": "WARNING",
                "body": tabularize(health_data)
            }
        elif health_data["status"] == "red":
            return {
                "severity": "FATAL",
                "body": tabularize(health_data),
                "title": "Health is RED"
            }
        else:
            return {
                "severity": "INFO",
                "body": tabularize(health_data),
                "title": "Health is Green"
            }
