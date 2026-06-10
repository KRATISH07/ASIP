from fastapi import HTTPException, status


class ASIPException(Exception):
    """Base exception for ASIP."""
    def __init__(self, message: str, code: str = "ASIP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(ASIPException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found.",
            code="NOT_FOUND"
        )


class PermissionDeniedError(ASIPException):
    def __init__(self, action: str = "perform this action"):
        super().__init__(
            message=f"You do not have permission to {action}.",
            code="PERMISSION_DENIED"
        )


class DuplicateError(ASIPException):
    def __init__(self, resource: str):
        super().__init__(
            message=f"{resource} already exists.",
            code="DUPLICATE"
        )


class WorkflowError(ASIPException):
    def __init__(self, message: str):
        super().__init__(message=message, code="WORKFLOW_ERROR")


# HTTP exception helpers
def not_found_http(resource: str, resource_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} '{resource_id}' not found."
    )


def unauthorized_http(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_http(detail: str = "Insufficient permissions") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )
