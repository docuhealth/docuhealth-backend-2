from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = response.data

        if isinstance(error_data, dict):
            message = error_data.get("detail", None)
            if not message:
                first_key = next(iter(error_data))
                message = error_data[first_key][0] if isinstance(error_data[first_key], list) else error_data[first_key]
        elif isinstance(error_data, list):
            message = error_data[0]
        else:
            message = str(error_data)

        return Response({
            "status": "error",
            "message": message,
            "error": {
                "type": exc.__class__.__name__,
                "errors": error_data, 
            }
        }, status=response.status_code)

    return Response({
        "status": "error",
        "message": str(exc) or "An unexpected error occurred",
        "error": {
            "type": exc.__class__.__name__,
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
