class AdvisorError(Exception):
    """Base exception for the financial advisor agent."""


class DataError(AdvisorError):
    pass


class SessionError(AdvisorError):
    pass


class GroqError(AdvisorError):
    pass
