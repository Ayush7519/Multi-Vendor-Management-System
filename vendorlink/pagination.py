from rest_framework.pagination import PageNumberPagination


# this is the class for the paganitation.
class MyPageNumberPaginationClass(PageNumberPagination):
    page_size = 10
