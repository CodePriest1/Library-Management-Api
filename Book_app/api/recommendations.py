from django.db.models import Count
from ..models import Loan, Books, Genre

def recommend_by_genre(user):
    borrowed_genres = Genre.objects.filter(
        books__loan__user=user
    ).distinct()

    borrowed_books = Loan.objects.filter(user=user).values_list("book_id", flat=True)
    return Books.objects.filter(
        genre__in=borrowed_genres
    ).exclude(id__in=borrowed_books).distinct()

def recommend_by_similarity(user):
    user_books = Loan.objects.filter(user=user).values_list("book_id", flat=True)
    other_users = Loan.objects.filter(book_id__in=user_books).exclude(user=user).values_list("user_id", flat=True)

    recommendations = (
        Loan.objects.filter(user_id__in=other_users)
        .exclude(book_id__in=user_books)
        .values("book_id")
        .annotate(count=Count("book_id"))
        .order_by("-count")
    )

    book_ids = [rec["book_id"] for rec in recommendations]
    return Books.objects.filter(id__in=book_ids)
