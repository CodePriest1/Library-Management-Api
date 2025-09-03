from django.urls import path
from Book_app.api.views import (BookListView, BookDetailView, LoanListView, UserActiveLoansView, AdminAllLoansView, ReturnLoanView, LoanDetailView, UserFineSummaryView, 
                                LoanFineAdminView, BulkBookUploadView, BulkLoanActionView, RecommendationView, BookAvailabilityView, AuditLogListView)
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns = [
    
    path('', BookListView.as_view(), name='book-list'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
    path('loans/', LoanListView.as_view(), name='loan-list'),
    path('loans/<int:pk>/', LoanDetailView.as_view(), name='loan-detail'),
    path('loans/<int:pk>/return/', ReturnLoanView.as_view(), name='return-loan'),
    path('my-active-loans/', UserActiveLoansView.as_view(), name='user-active-loans'),
    path('all-loans/', AdminAllLoansView.as_view(), name='admin-all-loans'),
    path("fines/", UserFineSummaryView.as_view(), name="user-fines"),
    path("admin/loans/<int:pk>/", LoanFineAdminView.as_view(), name="admin-loan-fines"),
    path("admin/books/import/", BulkBookUploadView.as_view(), name="bulk-book-import"),
    path("admin/loans/bulk-action/", BulkLoanActionView.as_view(), name="bulk-loan-action"),
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),
    path("books/<str:isbn>/availability/", BookAvailabilityView.as_view(), name="book-availability"),
    path("audit-logs/", AuditLogListView.as_view(), name="audit-logs"),




    # Your other endpoints...

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]



