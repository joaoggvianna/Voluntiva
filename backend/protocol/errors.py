class VAPError(Exception):
    code = 500
    label = "INTERNAL_ERROR"

class BadRequest(VAPError):
    code = 400
    label = "BAD_REQUEST"

class Unauthorized(VAPError):
    code = 401
    label = "UNAUTHORIZED"

class Forbidden(VAPError):
    code = 403
    label = "FORBIDDEN"

class NotFound(VAPError):
    code = 404
    label = "NOT_FOUND"

class Conflict(VAPError):
    code = 409
    label = "CONFLICT"

class PayloadTooLarge(VAPError):
    code = 413
    label = "PAYLOAD_TOO_LARGE"
