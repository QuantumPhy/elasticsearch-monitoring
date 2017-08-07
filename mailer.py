import smtplib
import re
import logging
from email.mime.text import MIMEText

try:
    import simplejson as json
except ImportError:
    import json

with open("mailer.json") as f:
    mailer = json.load(f)


def get_color_based_on_severity(severity):
    if severity.lower() == 'fatal':
        return 'red'
    if severity.lower() == 'warning':
        return 'yellow'
    return 'green'


def get_html_name(name):
    return re.sub("\s+", "_", name)


def format_item(item):
    return """
    <p>
      <table width='100%' border=0 cellpadding=12 cellspacing=0 name="{3}">
        <tr style='background-color:{1}'>
          <td align='center' style='font-size:18px;border:0'><b>{0}</b></td>
          <td style='width: 5%'><a href="#toc">Top</a></td>
        </tr>
        <tr>
          <td style='border:0'><pre>{2}</pre></td>
        </tr>
      </table>
    </p>
    """.format(
        item["title"],
        get_color_based_on_severity(item["severity"]),
        item["body"],
        get_html_name(item["title"])
    )


def build_toc(content):
    result = "<div id='toc' name='toc'><h3>Table of Contents</h3><ul><li>"
    result += "\n<li>".join(
        map(lambda c: '<a href="#{0}" />{1}</a>'.format(get_html_name(c["title"]), c["title"]), content)
    )
    result += "</ul></div>"
    return result


def mail(cluster, content):
    receivers = mailer["receivers"]

    if any(c["severity"] == "FATAL" for c in content):
        subject = "FATAL"
        actual_receivers = receivers.get("FATAL", []) + receivers.get("WARNING", []) + receivers.get("INFO", [])
        logging.info("Alerting FATAL error")
    elif any(c["severity"] == "WARNING" for c in content):
        subject = "WARNING"
        actual_receivers = receivers.get("WARNING", []) + receivers.get("INFO", [])
        logging.info("Alerting Warning")
    else:
        subject = "INFO"
        actual_receivers = receivers.get("INFO", [])
        logging.info("Alerting information")

    if actual_receivers:
        html = "<center><h1>{0} cluster monitoring alert</h1></center>".format(cluster) + \
               build_toc(content) + \
               "<br />".join(map(format_item, content))
        msg = MIMEText(html, "html")
        msg["Subject"] = "{0}: {1} cluster alert".format(subject, cluster)
        msg["From"] = mailer["sender"]
        msg["To"] = ",".join(actual_receivers)

        s = smtplib.SMTP(mailer["smtp_server"])
        s.sendmail(mailer["sender"], actual_receivers, msg.as_string())
        s.quit()
    else:
        logging.warn("No valid recipient list found to alert.")
