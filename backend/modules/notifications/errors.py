class NotificationsError(Exception):
    """Base error for notifications module."""


class WhatsAppDeliveryError(NotificationsError):
    pass


class InvalidRecipientError(NotificationsError):
    pass
