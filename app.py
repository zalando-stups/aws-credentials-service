#!/usr/bin/env python3
import logging
import re

import connexion
import requests

GROUPS_URL = 'https://users.auth.zalando.com/employees/{uid}/groups'
GROUP_PATTERN = 'cn={role_name},ou=Roles,ou=aws-[a-z]*-{account_id},ou=AWS,ou=apps,dc=zalando,dc=net'


def get_credentials(account_id: str, role_name: str):
    uid = connexion.request.user
    realm = connexion.request.token_info['realm']
    if realm != '/employees':
        return connexion.problem(403, 'Forbidden', 'You are not authorized to use this service')
    token = connexion.request.token_info['access_token']
    response = requests.get(GROUPS_URL.format(uid=uid), headers={'Authorization': 'Bearer {}'.format(token)})
    response.raise_for_status()
    groups = response.json()
    allowed = False
    for group in groups:
        if re.match(GROUP_PATTERN.format(role_name=role_name, account_id=account_id), group['dn']):
            allowed = True
            break
    if not allowed:
        return connexion.problem(403, 'Forbidden', 'Access to requested AWS account/role was denied')
    return allowed


logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__)
app.add_api('swagger.yaml')


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(port=8080, server='gevent')
