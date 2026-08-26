from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class GatewayAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_type: str = "invalid_request_error",
        code: Optional[str] = None,
        param: Optional[str] = None
    ):
        self.message = message
        self.error_type = error_type
        self.code = code or "BAD_REQUEST"
        self.param = param
        super().__init__(status_code=status_code, detail=message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "param": self.param,
                "code": self.code
            }
        }


class AuthenticationError(GatewayAPIException):
    def __init__(self, message: str = "Invalid or missing API key."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_type="authentication_error",
            code="INVALID_API_KEY"
        )


class PermissionDeniedError(GatewayAPIException):
    def __init__(self, message: str = "You do not have permission to access this resource or model."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_type="permission_error",
            code="FORBIDDEN"
        )


class InsufficientCreditsError(GatewayAPIException):
    def __init__(self, message: str = "Your wallet has insufficient credit balance. Please purchase credits to continue."):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            message=message,
            error_type="insufficient_credits",
            code="INSUFFICIENT_CREDITS"
        )


class RateLimitExceededError(GatewayAPIException):
    def __init__(self, retry_after: int = 60, message: str = "Rate limit exceeded. Please throttle your requests."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=f"{message} Retry after {retry_after} seconds.",
            error_type="rate_limit_error",
            code="RATE_LIMIT_EXCEEDED"
        )
        self.retry_after = retry_after


class ModelNotFoundError(GatewayAPIException):
    def __init__(self, model_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Model '{model_id}' does not exist or is currently disabled.",
            error_type="invalid_request_error",
            code="MODEL_NOT_FOUND",
            param="model"
        )


class ProviderError(GatewayAPIException):
    def __init__(self, message: str = "An error occurred while communicating with the upstream AI provider."):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_type="provider_error",
            code="UPSTREAM_PROVIDER_ERROR"
        )
