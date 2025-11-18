from rest_framework import status
from rest_framework.exceptions import APIException


class AppError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationError(AppError):
    def __init__(self, message="Validation error", details=None):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)
        self.details = details if details is not None else {}


class ConflictError(AppError):
    def __init__(self, message="Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)