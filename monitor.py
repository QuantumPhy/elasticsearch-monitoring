import logging.handlers

from allocations import allocations
from health import health
from shards import shards
from indices import indices
from mailer import mail
from master import get_master
from nodes import nodes
from os import mkdir

try:
    mkdir("logs")
except OSError:
    pass

LOG_FILENAME = "logs/es_monitor.log"
LOG_MSG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
LOG_DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

# Setup default stream logger
logging.basicConfig(level=logging.INFO, format=LOG_MSG_FORMAT, datefmt=LOG_DATE_FORMAT)

# Setup rotating log file handler
rotating_file_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1e7, backupCount=20)
rotating_file_handler.setFormatter(logging.Formatter(fmt=LOG_MSG_FORMAT, datefmt=LOG_DATE_FORMAT))
logging.root.addHandler(rotating_file_handler)

try:
    import simplejson as json
except ImportError:
    import json

with open("clusters.json") as f:
    logging.info("")
    logging.info("The Watch Dog wakes up")
    for cluster, config in json.load(f).iteritems():
        result = []
        logging.info("")
        logging.info("Begin processing Cluster [%s]", cluster)
        if not config.get("enabled", True):
            logging.info("Cluster [%s] is disabled", cluster)
            logging.info("End processing Cluster [%s]", cluster)
            continue
        try:
            master = get_master(cluster, config)
            master_host = master["host"]
            connection = master["connection"]
            logging.info("Cluster [%s] has a valid master [%s] in the config", cluster, master_host)
        except Exception as e:
            logging.error("Cluster [%s] does not have a valid master in the config", cluster)
            logging.info("End processing Cluster [%s]", cluster)
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

        logging.info("End processing Cluster [%s]", cluster)

    logging.info("The Watch Dog rests")
    logging.info("")
