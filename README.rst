=======================
AWS Credentials Service
=======================

**DISCLAIMER: This project is pre-alpha quality**

This very simple service takes an OAuth Bearer token,
checks the user's groups,
and returns temporary AWS credentials for the given account and role.

.. code-block:: bash

    $ docker build -t aws-credentials-service .
    $ docker run -it -p 8080:8080 \
      -e TOKENINFO_URL=https://tokeninfo.example.org/oauth2/tokeninfo \
      -e GROUPS_URL='https://users.example.org/employees/{uid}/groups' \
      -e GROUP_PATTERN='cn={role_name},ou=Roles,ou=aws-[a-z]*-{account_id},ou=AWS,ou=apps,dc=example,dc=org' \
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
``GROUP_PATTERN``
    Regex pattern template to match group DN to given account ID and role name
``ROLE_ARN``
    Optional: template for AWS role ARN to assume (defaults to ``arn:aws:iam::{account_id}:role/{role_name}``)


.. _tokeninfo mock: https://github.com/zalando/connexion/tree/master/examples/oauth2
.. _Plan B Token Info documentation: http://planb.readthedocs.io/en/latest/oauth2.html#introspection-endpoint
