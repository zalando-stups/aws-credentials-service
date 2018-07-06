=======================
AWS Credentials Service
=======================

.. image:: https://img.shields.io/badge/OpenTracing-enabled-blue.svg
   :target: http://opentracing.io
   :alt: OpenTracing enabled

This very simple service takes an OAuth Bearer token,
checks the user's groups,
and returns temporary AWS credentials for the given account and role.

.. code-block:: bash

    $ docker build -t aws-credentials-service .
    $ docker run -it -p 8080:8080 \
      -e TOKENINFO_URL=https://tokeninfo.example.org/oauth2/tokeninfo \
      -e GROUPS_URL='https://groups.example.org/employees/{uid}/groups' \
      aws-credentials-service

Swagger UI is now available on http://localhost:8080/ui/

Configuration
=============

The following environment variables are supported:

``TOKENINFO_URL``
    URL of OAuth tokeninfo endpoint, see `tokeninfo mock`_ and `Plan B Token Info documentation`_
``OAUTH2_ACCESS_TOKEN_URL``
    URL of OAuth Token Endpoint
``GROUPS_URL``
    URL to get list of user's groups
``ROLE_ARN``
    Optional: template for AWS role ARN to assume (defaults to ``arn:aws:iam::{account_id}:role/{role_name}``)
``OPENTRACING_TRACER``
    Optional: OpenTracing tracer name as supported by `opentracing-utils`_. Extra environment variables might be needed depending on the OpenTracing tracer used. Defaults to ``NOOP`` tracer.

The ``GROUPS_URL`` needs to return a JSON structure like:

.. code-block:: json

    [
    {"role": "PowerUser", "id": "123456789012", "name": "myacc"},
    {"role": "ReadOnly", "id": "456456789012", "name": "foobar"}
    ]


.. _tokeninfo mock: https://github.com/zalando/connexion/tree/master/examples/oauth2
.. _Plan B Token Info documentation: http://planb.readthedocs.io/en/latest/oauth2.html#introspection-endpoint
.. _opentracing-utils: https://github.com/zalando-zmon/opentracing-utils#init_opentracing_tracer
