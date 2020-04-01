#!/usr/bin/env python3

import gevent.monkey

gevent.monkey.patch_all()  # noqa

# Trace all outgoing requests
from opentracing_utils import trace_requests

trace_requests()  # noqa

import boto3
import logging
import os

import connexion
import re
import requests
import tokens
import audittrail

from opentracing_utils import init_opentracing_tracer, trace
from opentracing_utils import trace_flask, extract_span_from_flask_request

GROUPS_URL = os.getenv('GROUPS_URL')
ROLE_ARN = os.getenv('ROLE_ARN', 'arn:aws:iam::{account_id}:role/{role_name}')
ROLE_SESSION_NAME_INVALID_CHARS = re.compile(r'[^\w+=,.@-]')
GROUP_NAME = re.compile(r"^Apps/AWS/Aws-(?P<account_name>[-\w]+)-(?P<account_id>\d+)/Roles/(?P<role_name>\w+)$")

logging.basicConfig(level=logging.INFO)
logging.getLogger('connexion.api.security').setLevel(logging.WARNING)
logging.getLogger('botocore.vendored').setLevel(logging.WARNING)
logger = logging.getLogger('aws-credentials-service')

tokens.configure(from_file_only=True)
tokens.manage('uid')
tokens.start()

audittrail_client = audittrail.AuditTrail(os.getenv('AUDITTRAIL_URL'), 'uid', tokens)


def parse_groups(groups):
    for group in groups:
        if "provider" in group:
            # /accounts/aws API
            yield {
                "account_id": group["id"],
                "account_name": group["name"],
                "role_name": group["role"],
            }
        else:
            # /groups API
            match = GROUP_NAME.fullmatch(group["name"])
            if not match:
                continue

            yield {
                "account_id": match.group("account_id"),
                "account_name": match.group("account_name").lower(),
                "role_name": match.group("role_name"),
            }


@trace()
def get_roles(username):
    token = tokens.get('uid')
    response = requests.get(GROUPS_URL.format(uid=username), headers={'Authorization': 'Bearer {}'.format(token)})
    response.raise_for_status()
    return list(parse_groups(response.json()))


def get_account_roles(user_id):
    current_span = extract_span_from_flask_request()
    return {'account_roles': get_roles(user_id, parent_span=current_span)}


def get_credentials(account_id: str, role_name: str, user: str, token_info: dict):
    current_span = extract_span_from_flask_request()

    uid = user
    realm = token_info['realm']

    if realm != '/employees':
        return connexion.problem(403, 'Forbidden', 'You are not authorized to use this service')
    try:
        roles = get_roles(uid)
    except Exception as e:
        current_span.log_kv({'exception': str(e)})
        logger.exception('Failed to get groups for {}'.format(uid))
        return connexion.problem(500, 'Server Error', 'Failed to get groups: {}'.format(e))

    allowed = False
    for account_role in roles:
        if role_name == account_role['role_name'] and account_id == account_role['account_id']:
            allowed = True
            break
    if not allowed:
        current_span.set_tag('allowed', False)
        return connexion.problem(403, 'Forbidden', 'Access to requested AWS account/role was denied')

    sts = boto3.client('sts')
    arn = ROLE_ARN.format(account_id=account_id, role_name=role_name)
    role_session_name = ROLE_SESSION_NAME_INVALID_CHARS.sub('', uid)

    try:
        role = sts.assume_role(RoleArn=arn, RoleSessionName=role_session_name)
    except Exception as e:
        error_message = 'Failed to assume role: {}'.format(e)
        current_span.log_kv({'exception': str(e), 'role_arn': arn})
        if 'AccessDenied' in error_message:
            # role might not exist in target account
            logger.error(error_message)
            return connexion.problem(403, 'AWS Error', error_message)
        else:
            # something else happened
            current_span.set_tag('error', True)
            logger.exception('Failed to assume role {}'.format(arn))
            return connexion.problem(500, 'AWS Error', error_message)

    credentials = role['Credentials']
    logger.info(
        'Handing out credentials for {account_id}/{role_name} to {uid}'.format(
            account_id=account_id, role_name=role_name, uid=uid))
    audittrail_client.request_aws_credentials(user, realm, account_id, role_name)

    return {'access_key_id': credentials['AccessKeyId'],
            'secret_access_key': credentials['SecretAccessKey'],
            'session_token': credentials['SessionToken'],
            'expiration': credentials['Expiration']}


app = connexion.App(__name__)
app.add_api('swagger.yaml')

if __name__ == '__main__':
    tracer = os.getenv('OPENTRACING_TRACER')
    logger.info('Starting server with OpenTracing tracer: {}'.format(tracer))

    init_opentracing_tracer(tracer)

    # Trace all incoming requests
    trace_flask(app.app)

    # run our standalone gevent server
    app.run(port=8080, server='gevent')
