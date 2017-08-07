import logging.handlers

from allocations import allocations
from health import health
from shards import shards
from indices import indices
from mailer import mail
from master import get_master
from nodes import nodes

LOG_FILENAME = "es_monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)
logger = logging.getLogger("ES_MONITOR")
logger.setLevel(logging.INFO)
logger.addHandler(logging.handlers.RotatingFileHandler(LOG_FILENAME, 1e7, 20))

try:
    import simplejson as json
except ImportError:
    import json

with open("clusters.json") as f:
    for cluster, config in json.load(f).iteritems():
        result = []
        logger.info("")
        logger.info("Processing Cluster [%s]", cluster)
        if not config.get("enabled", True):
            logger.info("Cluster [%s] is disabled", cluster)
            continue
        try:
            master = get_master(cluster, config)
            master_host = master["host"]
            connection = master["connection"]
            logger.info("Cluster [%s] has a valid master [%s] in the config", cluster, master_host)
        except Exception as e:
            logger.error("Cluster [%s] does not have a valid master in the config", cluster)
            result.append(
                {
                    "title": "No valid elasticsearch instance in the configuration",
                    "severity": "FATAL",
                    "body": "<br />".join(config["eshosts"].split(","))
                }
            )
            mail(cluster, result)
            continue

        cluster_health = health(connection, config)
        result.append(cluster_health)

        # These metrics are not alarming if the cluster health is good
        result.append(indices(connection, config, cluster_health["severity"]))
        result.append(shards(connection, config, cluster_health["severity"]))

        # These metrics are alarming irrespective of the cluster health
        result.append(allocations(connection, config))
        result.append(nodes(cluster, connection, config))

        if any(item['severity'] != "INFO" for item in result):
            mail(cluster, result)
