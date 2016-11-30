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
