# Shared DRF pagination class used by all list viewsets.
# Reports and dropdowns that call list endpoints without a 'page' param
# are NOT paginated — they receive the full queryset as before.

from rest_framework.pagination import PageNumberPagination

PAGE_SIZE = 25


class StandardPageNumberPagination(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = "page_size"
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        # Skip pagination entirely when no 'page' param is present.
        # This keeps existing report endpoints and FK-dropdown callers working
        # without any changes on their side.
        if self.page_query_param not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)
