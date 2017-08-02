import smtplib
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


def format_item(item):
    return """
    <p>
      <table width='100%' border=0 cellpadding=12 cellspacing=0>
        <tr style='background-color:{1}'>
          <td align='center' style='font-size:18px;border:0'><b>{0}</b></td>
        </tr>
        <tr>
          <td style='border:0'>{2}</td>
        </tr>
      </table>
    </p>
    """.format(
        item["title"],
        get_color_based_on_severity(item["severity"]),
        item["body"]
    )


def mail(cluster, content):
    html = "<center><h1>{0} cluster monitoring alert</h1></center>".format(cluster) + \
        "<br />".join(map(format_item, content))
    msg = MIMEText(html, "html")
    msg["Subject"] = "{0} cluster alert".format(cluster)
    msg["From"] = mailer["sender"]
    msg["To"] = ",".join(mailer["receivers"])
    s = smtplib.SMTP(mailer["smtp_server"])
    s.sendmail(mailer["sender"], mailer["receivers"], msg.as_string())
    s.quit()
