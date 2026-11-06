class ProviderError(RuntimeError):
    retryable = False


class ProviderThrottle(ProviderError):
    retryable = True


class ProviderTimeout(ProviderError):
    retryable = True


class ProviderUnavailable(ProviderError):
    retryable = True


class ProviderMalformed(ProviderError):
    retryable = False
