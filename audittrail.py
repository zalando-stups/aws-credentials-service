class AuditTrail:
    """Defines a client for sending events to AuditTrail"""

    namespace = 'cloud.zalando.com'
    event_name = 'request-aws-credentials'
    version = '1.0'

    def __init__(self, url, tokenSource):
        self.url = url
        self.tokenSource = tokenSource

    def send(context, event):
        pass

    def request_aws_credentials(user, account):
        event = {"event_type": { "namespace": namespace,
                                 "name": event_name,
                                 "varsion": version,
                               }
                }

        return event
