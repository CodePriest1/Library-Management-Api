from django.shortcuts import render
from Book_app.models import Books, Loan, AuditLog
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.generics import ListAPIView
from Book_app.api.serializers import BookSerializer, LoanSerializer, UserFineSummarySerializer, BulkBookUploadSerializer, BulkLoanActionSerializer, AuditLogSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics
import csv, io
from datetime import timedelta
from .recommendations import recommend_by_genre, recommend_by_similarity
from .audit import log_action
from django.utils.dateparse import parse_datetime
# Create your views here.

class BookListView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated]
    queryset = Books.objects.all()
    serializer_class = BookSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'author', 'genre']


    def get_queryset(self):
        queryset = super().get_queryset()
        library_id = self.request.query_params.get("library_id")  # e.g. /api/books/?library_id=2
        if library_id:
            queryset = queryset.filter(library_id=library_id)
        return queryset
    
    def perform_create(self, serializer):
        book = serializer.save()
        log_action(self.request.user, "BOOK_CREATED", f"Book ID {book.id} - {book.title}")

    
    
class UserActiveLoansView(ListAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        loans = Loan.objects.filter(user=request.user, return_date__isnull=True)
        if loans:
            serializer = LoanSerializer(loans, many=True)
            return Response(serializer.data)
        return Response({"detail": "No active loans found."}, status=status.HTTP_404_NOT_FOUND)
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user, return_date__isnull=True)
      
    
class AdminAllLoansView(ListAPIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        loans = Loan.objects.all()
        serializer = LoanSerializer(loans, many=True)
        return Response(serializer.data)
    
class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Books.objects.all()
    serializer_class = BookSerializer
    # permission_classes = [IsAuthenticated]


    def get_permissions(self):
        # Only admin can delete, others can read/update
        if self.request.method == 'DELETE':
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    
class LoanListView(generics.ListCreateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    
    def get_permissions(self):
        """
        Customizes permissions based on the request method.
        Only authenticated users can create a loan (POST).
        Only admin users can view the list of all loans (GET).
        """
        # For a POST request (creating a loan), only the user needs to be authenticated.
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        
        # For a GET request (listing loans), only an admin user can proceed.
        # The queryset will then be filtered in get_queryset.
        return [IsAdminUser()]

    def get_queryset(self):
        """
        Customizes the queryset to be returned based on the user's permissions.
        Admins see all loans; regular users see only their own.
        """
        # The get_permissions method above already ensures that
        # only admins can make it this far for a GET request.
        # Therefore, we can safely return all loans here.
        if self.request.user.is_staff:
            return Loan.objects.all()
        
        # For a user who is not an admin, return only their loans.
        # This branch is technically unreachable for a GET request due to the permissions check,
        # but it's good practice to have the logic here for clarity and in case permissions change.
        return Loan.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Customizes the create action to check for book availability
        and decrease the book count upon successful loan creation.
        """
        book = serializer.validated_data.get('book')

        if not book:
            raise ValidationError("Book field is required.")
        
        # Check if there are available copies before creating the loan
        if book.available_no_of_books <= 0:
            raise ValidationError("No available copies of this book.")

        # Save the loan with the current user and selected book
        loan = serializer.save(user=self.request.user, book=book)

        # Atomically reduce the available book count to prevent race conditions
        book.available_no_of_books -= 1
        book.save(update_fields=['available_no_of_books'])

class UserFineSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        loans = Loan.objects.filter(user=request.user)

        total_fines = 0
        total_paid = 0

        for loan in loans:
            loan.update_fine()  # <-- force update before summing
            total_fines += loan.fine_amount
            total_paid += loan.fine_paid

        outstanding_balance = total_fines - total_paid

        data = {
            "total_fines": total_fines,
            "total_paid": total_paid,
            "outstanding_balance": outstanding_balance,
        }
        serializer = UserFineSummarySerializer(data)
        return Response(serializer.data)


class LoanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Only the user who created the loan can update or delete it
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def perform_update(self, serializer):
        # Ensure that only the user who created the loan can update it
        if self.request.user != serializer.instance.user:
            raise PermissionError("You do not have permission to update this loan.")
        serializer.save()
        
class LoanFineAdminView(generics.UpdateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins

    def patch(self, request, *args, **kwargs):
        """
        Admin can PATCH a loan to update fine_paid (mark as paid/waived).
        Example payload:
        {
            "fine_paid": 10
        }
        """
        return super().patch(request, *args, **kwargs)

class ReturnLoanView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Loan.objects.get(pk=pk)
        except Loan.DoesNotExist:
            return None
     
    def post(self, request, pk):
        try:
            loan = Loan.objects.get(pk=pk)
            loan.mark_as_returned()
            return Response({'detail': 'Book returned successfully.'})
        except Loan.DoesNotExist:
            return Response({'detail': 'Loan not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class BulkBookUploadView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = BulkBookUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created_books = []
        errors = []

        for row in reader:
            # Example CSV fields: title, author, isbn, available_no_of_books
            isbn = row.get("isbn")
            if Books.objects.filter(isbn=isbn).exists():
                errors.append(f"Duplicate ISBN: {isbn}")
                continue

            book_data = {
                "title": row.get("title"),
                "author": row.get("author"),
                "isbn": isbn,
                "available_no_of_books": int(row.get("available_no_of_books", 1))
            }

            book_serializer = BookSerializer(data=book_data)
            if book_serializer.is_valid():
                book_serializer.save()
                created_books.append(book_serializer.data)
            else:
                errors.append(book_serializer.errors)

        return Response(
            {"created": created_books, "errors": errors},
            status=status.HTTP_201_CREATED if created_books else status.HTTP_400_BAD_REQUEST
        )
        
        


class BulkLoanActionView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = BulkLoanActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        loan_ids = serializer.validated_data["loan_ids"]
        action = serializer.validated_data["action"]
        extension_days = serializer.validated_data.get("extension_days", 0)

        loans = Loan.objects.filter(id__in=loan_ids)
        updated = []
        errors = []

        for loan in loans:
            if action == "return":
                loan.returned = True
                loan.save()
                updated.append({"id": loan.id, "status": "returned"})
            elif action == "extend":
                if loan.returned:
                    errors.append({"id": loan.id, "error": "Already returned"})
                else:
                    loan.due_date += timedelta(days=extension_days)
                    loan.save()
                    updated.append({"id": loan.id, "status": f"extended {extension_days} days"})

        return Response({"updated": updated, "errors": errors})


class RecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Combine both strategies
        genre_recs = recommend_by_genre(request.user)[:5]
        similar_recs = recommend_by_similarity(request.user)[:5]

        combined = (genre_recs | similar_recs).distinct()[:10]
        serializer = BookSerializer(combined, many=True)
        return Response(serializer.data)

        
class BookAvailabilityView(APIView):
    def get(self, request, isbn):
        data = Books.availability_across_branches(isbn)
        return Response(data)
    

class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        user_id = self.request.query_params.get("user")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if user_id:
            queryset = queryset.filter(user__id=user_id)
        if start_date:
            queryset = queryset.filter(timestamp__gte=parse_datetime(start_date))
        if end_date:
            queryset = queryset.filter(timestamp__lte=parse_datetime(end_date))

        return queryset
# class RegisterUserView(ListAPIView):
#     def post(self, request):
#         serializer = userSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)