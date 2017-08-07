import logging
from tabularize_json import tabularize, json
logger = logging.getLogger("HEALTH")


def health(con, config):
    r1 = con("/_cat/health")
    response = r1.read()
    if r1.status != 200:
        return {
            "severity": "FATAL",
            "title": "Health Check Failed with HTTP Code [{0}]".format(r1.status),
            "body": tabularize(response)
        }
    else:
        health_data = json.loads(response)[0]
        if health_data["status"] == "yellow":
            result = {
                "title": "Health is Yellow",
                "severity": "WARNING",
                "body": tabularize(health_data)
            }
        elif health_data["status"] == "red":
            result = {
                "severity": "FATAL",
                "body": tabularize(health_data),
                "title": "Health is RED"
            }
        else:
            result = {
                "severity": "INFO",
                "body": tabularize(health_data),
                "title": "Health is Green"
            }

        if not config.get("health_check", True):
            result["severity"] = "INFO"

        return result
