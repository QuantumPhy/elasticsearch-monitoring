import smtplib
import re
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
    html = "<center><h1>{0} cluster monitoring alert</h1></center>".format(cluster) + \
           build_toc(content) + \
           "<br />".join(map(format_item, content))
    msg = MIMEText(html, "html")

    if any(c["severity"] == "FATAL" for c in content):
        msg["Subject"] = "FATAL: {0} cluster alert".format(cluster)
    elif any(c["severity"] == "WARNING" for c in content):
        msg["Subject"] = "WARNING: {0} cluster alert".format(cluster)
    else:
        msg["Subject"] = "INFO: {0} cluster alert".format(cluster)

    msg["From"] = mailer["sender"]
    msg["To"] = ",".join(mailer["receivers"])

    s = smtplib.SMTP(mailer["smtp_server"])
    s.sendmail(mailer["sender"], mailer["receivers"], msg.as_string())
    s.quit()
