#!/usr/bin/env python3
import logging

import connexion


def get_credentials(account_id: str, role_name: str):
    pass

logging.basicConfig(level=logging.INFO)
app = connexion.App(__name__)
app.add_api('swagger.yaml')


if __name__ == '__main__':
    # run our standalone gevent server
    app.run(port=8080, server='gevent')
