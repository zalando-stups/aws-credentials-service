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

from opentracing_utils import init_opentracing_tracer, trace
from opentracing_utils import trace_flask, extract_span_from_flask_request


GROUPS_URL = os.getenv('GROUPS_URL')
ROLE_ARN = os.getenv('ROLE_ARN', 'arn:aws:iam::{account_id}:role/{role_name}')
ROLE_SESSION_NAME_INVALID_CHARS = re.compile('[^\w+=,.@-]')

logging.basicConfig(level=logging.INFO)
logging.getLogger('connexion.api.security').setLevel(logging.WARNING)
logging.getLogger('botocore.vendored').setLevel(logging.WARNING)
logger = logging.getLogger('aws-credentials-service')

tokens.configure()
tokens.manage('uid', ['uid'])
tokens.start()


@trace()
def get_groups(uid):
    token = tokens.get('uid')
    response = requests.get(GROUPS_URL.format(uid=uid), headers={'Authorization': 'Bearer {}'.format(token)})
    response.raise_for_status()
    groups = [g for g in response.json() if not g.get('disabled')]
    return groups


def map_group_to_account_role(group):
    return {'account_id': group['id'], 'role_name': group['role'], 'account_name': group['name']}


def get_account_roles(user_id):
    current_span = extract_span_from_flask_request()

    groups = get_groups(user_id, parent_span=current_span)
    account_roles = list(map(map_group_to_account_role, groups))
    return {'account_roles': account_roles}


def get_credentials(account_id: str, role_name: str, user: str, token_info: dict):
    current_span = extract_span_from_flask_request()

    uid = user
    realm = token_info['realm']

    if realm != '/employees':
        return connexion.problem(403, 'Forbidden', 'You are not authorized to use this service')
    try:
        groups = get_groups(uid)
    except Exception as e:
        current_span.log_kv({'exception': str(e)})
        logger.exception('Failed to get groups for {}'.format(uid))
        return connexion.problem(500, 'Server Error', 'Failed to get groups: {}'.format(e))

    allowed = False
    for account_role in map(map_group_to_account_role, groups):
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
        current_span.log_kv({'exception': str(e), 'role_arn': arn})
        logger.exception('Failed to assume role {}'.format(arn))
        return connexion.problem(500, 'AWS Error', 'Failed to assume role: {}'.format(e))

    credentials = role['Credentials']
    logger.info(
        'Handing out credentials for {account_id}/{role_name} to {uid}'.format(
            account_id=account_id, role_name=role_name, uid=uid))

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
