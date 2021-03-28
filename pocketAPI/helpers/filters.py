from collections import Iterable

import coreschema
import coreapi

from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class CustomFilterBackend(BaseFilterBackend):
    """
        Custom filter backend.
    """

    def filter_queryset(self, request, queryset, view):
        """
            Return a filtered queryset.
        """
        filter_fields = getattr(view, 'filter_fields', {})
        if not filter_fields:
            return queryset
        else:
            filters = Q()
            for field, info in filter_fields.items():
                if field in request.query_params:
                    filters &= Q(**{field: request.query_params[field]})
            return queryset.filter(filters)

    def get_schema_fields(self, view):
        assert (
            coreapi is not None
        ), "coreapi must be installed to use `get_schema_fields()`"
        assert (
            coreschema is not None
        ), "coreschema must be installed to use `get_schema_fields()`"

        fields = getattr(view, 'filter_fields', {})
        if not isinstance(fields, dict):
            raise ValueError('filter_fields must be dict')

        return [
            coreapi.Field(
                name=field_key,
                location='query',
                required=field_values.get('required', False),
                type=field_values.get('type', 'string'),
                description=field_values.get('description', ''),
                example=field_values.get('example', ''),
                schema=field_values.get('schema', None),
            ) for field_key, field_values in fields.items()
        ]
