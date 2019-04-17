import datetime

class AuditTrail:
    """Defines a client for sending events to AuditTrail"""

    event_type = {
        "namespace": "cloud.zalando.com",
        "name": "request-aws-credentials",
        "version": "1.0",
    }

    def __init__(self, url, tokenSource):
        self.url = url
        self.tokenSource = tokenSource

    def send(context, event):
        pass

    def request_aws_credentials(self, user, realm, account_id, role):
        event = {
            "event_type": self.event_type,
            "triggered_at": datetime.datetime.utcnow(),
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

        return event
