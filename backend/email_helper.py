import boto3
import botocore
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

with open('settings.conf.json') as f:
    settings = json.load(f)


def send_ses_email(email_addr, subject, text, from_email_addr=None):
    ses_cred = settings['SES_CREDENTIALS']
    ses_client = boto3.client(
        service_name='ses',
        region_name=ses_cred["region"],
        aws_access_key_id=ses_cred['accessKeyId'],
        aws_secret_access_key=ses_cred["secretAccessKey"]
    )
    email_subject = subject
    email_text = text
    email_recipient = email_addr
    msg_container = MIMEMultipart('mixed')
    msg_container['Subject'] = email_subject
    msg_container['From'] = ses_cred["from"] if not from_email_addr else from_email_addr
    msg_container['To'] = email_recipient
    # inner alternative container
    msg_inner = MIMEMultipart('alternative')
    textpart = MIMEText(email_text.encode('utf-8'), 'plain', 'utf-8')
    msg_inner.attach(textpart)
    msg_container.attach(msg_inner)
    response_data = None
    try:
        response = ses_client.send_raw_email(
            Destinations=[
                email_recipient
            ],
            RawMessage={
                'Data': msg_container.as_string(),
            },
            Source=ses_cred["from"]
        )
    except botocore.exceptions.ClientError as e:
        response_data = {
            "code": e.response['Error']['Code'],
            "msg": e.response['Error']['Message'],
            "requestid": e.response['ResponseMetadata']['RequestId'],
            "http_code": e.response['ResponseMetadata']['HTTPStatusCode']
        }
        print(response_data)
        return False
    else:
        response_data = response
    print(response_data)
    return True
