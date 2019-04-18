import datetime
import hashlib
import json
import logging
import requests
import requests.exceptions

logger = logging.getLogger('aws-credentials-service')

class AuditTrail:
    """Defines a client for sending events to AuditTrail"""

    event_type = {
        "namespace": "cloud.zalando.com",
        "name": "request-aws-credentials",
        "version": "1.0",
    }

    def __init__(self, url, token_name, token_source):
        self.session = requests.Session()
        self.url = url + "/events/{}"
        self.token_name = token_name
        self.token_source = token_source

    def __send(self, event):
        payload = json.dumps(event, sort_keys=True)
        event_id = hashlib.sha1(payload.encode()).hexdigest()

        self.__send_to_audit_trail(event_id, event["event_type"]["name"], payload)

    def __send_to_audit_trail(self, event_id, event_name, payload):
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(self.token_source.get(self.token_name)),
        }

        try:
            r = self.session.put(self.url.format(event_id), data=payload, headers=headers)
            r.raise_for_status()
        except Exception as e:
            logger.exception("Failed to push event ({})".format(e))

    def request_aws_credentials(self, user, realm, account_id, role):
        event = {
            "event_type": self.event_type,
            "triggered_at": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
            "triggered_by": {
                "type": "USER",
                "id": user,
                "additional": {
                    "realm": realm,
                },
            },
            "payload": {
                "user": user,
                "account_id": account_id,
                "role": role,
            }
        }

        self.__send(event)
