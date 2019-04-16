class AuditTrail:
    """Defines a client for sending events to AuditTrail"""

    namespace = 'cloud.zalando.com'
    event = 'request-aws-credentials'
    version = '1.0'

    def __init__(self, url, tokenSource):
        self.url = url
        self.tokenSource = tokenSource

    def send(context, event)
