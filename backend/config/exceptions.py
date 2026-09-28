from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from config.errors import DomainError
from hospital.services import HospitalError


def api_exception_handler(exc, context):
    
    if isinstance(exc, DomainError):
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "error_dict") else exc.messages
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
    return exception_handler(exc, context)
