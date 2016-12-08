#!/usr/bin/env python3

import gevent.monkey
gevent.monkey.patch_all()


import boto3
import logging
import os
import re

import connexion
import requests
import tokens

GROUPS_URL = os.getenv('GROUPS_URL')
GROUP_PATTERN = os.getenv('GROUP_PATTERN')
ROLE_ARN = os.getenv('ROLE_ARN', 'arn:aws:iam::{account_id}:role/{role_name}')

logging.basicConfig(level=logging.INFO)
logging.getLogger('connexion.api.security').setLevel(logging.WARNING)
logging.getLogger('botocore.vendored').setLevel(logging.WARNING)
logger = logging.getLogger('aws-credentials-service')

tokens.configure()
tokens.manage('uid', ['uid'])
tokens.start()


def get_credentials(account_id: str, role_name: str):
    uid = connexion.request.user
    realm = connexion.request.token_info['realm']
    if realm != '/employees':
        return connexion.problem(403, 'Forbidden', 'You are not authorized to use this service')
    token = tokens.get('uid')
    try:
        response = requests.get(GROUPS_URL.format(uid=uid), headers={'Authorization': 'Bearer {}'.format(token)})
        response.raise_for_status()
        groups = response.json()
    except Exception as e:
        logger.exception('Failed to get groups for {}'.format(uid))
        return connexion.problem(500, 'Server Error', 'Failed to get groups: {}'.format(e))
    allowed = False
    for group in groups:
        if re.match(GROUP_PATTERN.format(role_name=role_name, account_id=account_id), group['dn']):
            allowed = True
            break
    if not allowed:
        return connexion.problem(403, 'Forbidden', 'Access to requested AWS account/role was denied')
    sts = boto3.client('sts')
    arn = ROLE_ARN.format(account_id=account_id, role_name=role_name)
    try:
        role = sts.assume_role(RoleArn=arn, RoleSessionName='aws-credentials-service')
    except Exception as e:
        logger.exception('Failed to assume role {}'.format(arn))
        return connexion.problem(500, 'AWS Error', 'Failed to assume role: {}'.format(e))
    credentials = role['Credentials']
    logger.info('Handing out credentials for {account_id}/{role_name} to {uid}'.format(account_id=account_id, role_name=role_name, uid=uid))

    return {'access_key_id': credentials["AccessKeyId"],
            'secret_access_key': credentials["SecretAccessKey"],
            'session_token': credentials["SessionToken"]}


app = connexion.App(__name__)
app.add_api('swagger.yaml')


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(port=8080, server='gevent')
