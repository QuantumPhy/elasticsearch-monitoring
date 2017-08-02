import logging
import logging.handlers
from health import health
from master import get_master
from mailer import mail
from inactive_shards import inactive_shards

LOG_FILENAME = "es_monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)
logger = logging.getLogger("ES_MONITOR")
logger.setLevel(logging.INFO)
logger.addHandler(logging.handlers.RotatingFileHandler(LOG_FILENAME, 1e3, 20))

try:
    import simplejson as json
except ImportError:
    import json

with open("clusters.json") as f:
    for cluster, config in json.load(f).iteritems():
        result = []
        logger.info("")
        logger.info("")
        logger.info("Processing Cluster [%s]", cluster)
        try:
            master = get_master(cluster, config)
            master_host = master["host"]
            connection = master["connection"]
            logger.info("Cluster [%s] has a valid master [%s] in the config", cluster, master_host)
        except:
            logger.error("Cluster [%s] does not have a valid master in the config", cluster)
            result.append(
                {
                    "title": "No valid elasticsearch instance in the configuration",
                    "severity": "FATAL",
                    "body": "<br />".join(config["eshosts"].split(","))
                }
            )
            continue

        result.append(health(cluster, connection))
        result.append(inactive_shards(cluster, connection))
        # from pprint import pprint
        # pprint(result)
        # if any(item['severity'] != "INFO" for item in result):
        #     mail(cluster, result)
        mail(cluster, result)
