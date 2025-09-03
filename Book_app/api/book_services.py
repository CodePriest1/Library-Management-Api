from django.db.models import Sum
from ..models import Books

def availability_across_branches(isbn):
    return (
        Books.objects.filter(isbn=isbn)
        .values("library__name")
        .annotate(
            total=Sum("total_no_of_books"),
            available=Sum("available_no_of_books")
        )
    )
