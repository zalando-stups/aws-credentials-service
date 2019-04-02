AUDIT_NAMESPACE = 'cloud.zalando.com'
REQUEST_AWS_CREDENTIALS_VERSION = '1.0'
REQUEST_AWS_CREDENTIALS_EVENT = 'request-aws-credentials'

class AuditTrail:
    """Defines a client for sending events to AuditTrail"""

    def __init__(self, url, tokenSource):
        self.url = url
        self.tokenSource = tokenSource
