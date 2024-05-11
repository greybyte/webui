import ssl
from pathlib import Path
from smtplib import SMTP, SMTP_SSL, SMTPResponseException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from json import dumps as json_dumps

from aw.base import USERS
from aw.utils.util import valid_email
from aw.utils.debug import log
from aw.config.main import config
from aw.model.job import JobExecution
from aw.settings import get_main_web_address
from aw.model.system import MAIL_TRANSPORT_TYPE_SSL, MAIL_TRANSPORT_TYPE_STARTTLS


def _email_send(server: SMTP, user: USERS, stats: list[dict], execution: JobExecution):
    server.login(user=config['mail_user'], password=config['mail_pass'])
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Ansible WebUI Alert - Job '{execution.job.name}' - {execution.status_name}"
    msg['From'] = config['mail_sender']
    msg['To'] = user.email

    text = f"""
Job: {execution.job.name}
Status: {execution.status_name}

Executed by: {execution.user_name}
Start time: {execution.time_created_str}
"""

    if execution.result is not None:
        text += f"""
Finish time: {execution.result.time_fin_str}
Duration: {execution.result.time_duration_str}
"""

        if execution.result.error is not None:
            text += f"""
Short error message: '{execution.result.error.short}'
Long error message: '{execution.result.error.med}'
"""

    for log_attr in JobExecution.log_file_fields:
        file = getattr(execution, log_attr)
        if Path(file).is_file():
            text += f"""
{log_attr.replace('_', ' ').capitalize()}: {get_main_web_address()}{getattr(execution, log_attr + '_url')}
"""

    if len(stats) > 0:
        text += f"""

Raw stats:
{json_dumps(stats)}
"""

    msg.attach(MIMEText(text, 'plain'))
    # msg.attach(MIMEText(html, 'html'))

    server.sendmail(
        from_addr=config['mail_sender'],
        to_addrs=user.email,
        msg=msg.as_string()
    )


def alert_plugin_email(user: USERS, stats: list[dict], execution: JobExecution):
    if user.email.endswith('@localhost') or not valid_email(user.email):
        log(msg=f"User has an invalid email address configured: {user.username} ({user.email})", level=3)
        return

    try:
        server, port = config['mail_server'].split(':', 1)

    except ValueError:
        server = config['mail_server']
        port = 25

    try:
        print(f"Alert user {user.username} via email ({server}:{port} => {user.email})")
        ssl_context = ssl.create_default_context()
        if config['mail_ssl_verify']:
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

        else:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        if config['mail_transport'] == MAIL_TRANSPORT_TYPE_SSL:
            with SMTP_SSL(server, port, context=ssl_context) as server:
                server.login(config['mail_user'], config['mail_pass'])
                _email_send(server=server, user=user, stats=stats, execution=execution)

        else:
            with SMTP(server, port) as server:
                if config['mail_transport'] == MAIL_TRANSPORT_TYPE_STARTTLS:
                    server.starttls(context=ssl_context)

                _email_send(server=server, user=user, stats=stats, execution=execution)

    except (SMTPResponseException, OSError) as e:
        log(msg=f"Got error sending alert mail: {e}", level=2)
