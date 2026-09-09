class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str, code: str | None = None):
        self.detail = detail
        self.code = code or self.__class__.__name__
        super().__init__(detail)


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
