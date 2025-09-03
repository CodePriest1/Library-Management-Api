from django.db import models
# from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

# Create your models here.

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Library(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name
    
    
class Books(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    publication_year = models.IntegerField()
    genre = models.ManyToManyField(Genre, related_name="books")
    total_no_of_books = models.IntegerField()
    available_no_of_books = models.IntegerField(default=0)  # This will be calculated based on loans
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name="books")

    # def available_copies(self):
    #     return self.available_no_of_books
    
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.available_no_of_books= self.total_no_of_books
        super().save(*args, **kwargs)
        
        
    def __str__(self):
        return self.title 
    
    
    class Meta:
        verbose_name_plural = "Books"
    
    
    def available_copies(self):
        return self.total_no_of_books - Loan.objects.filter(book=self, return_date__isnull=True).count()
        
    
    def is_available(self):
        return self.available_copies > 0
    
    
# class User(models.Model):
#     username = models.CharField(max_length=50, unique=True)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=100)
    
#     def __str__(self):
#         return self.username 
    
#     class Meta:
#         verbose_name_plural = "Users" 
def get_due_date():
    return timezone.now().date() + timedelta(days=7)
        
        
class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE, null=False, blank=False)
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name="loans")
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(default=get_due_date)
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0)  
    fine_paid = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    DAILY_FINE_AMOUNT = 1 # Assuming a fine of $1 per day
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
    
    class Meta:
        verbose_name_plural = "Loans"
        
    def update_fine(self):
        """Recalculate fine based on overdue days."""
        if self.is_overdue():
            overdue_days = (timezone.now().date() - self.due_date).days
            self.fine_amount = overdue_days * self.DAILY_FINE_AMOUNT
        else:
            self.fine_amount = 0
        self.save()

    
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.return_date:
            if self.book.available_no_of_books > 0:
                self.book.available_no_of_books -= 1
                self.book.save()
            else:
                raise ValueError("No copies available for loan.")
        # if not self.due_date:
        #     self.due_date = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)
        
        
    def is_overdue(self):
        return self.return_date is None and timezone.now().date() > self.due_date
    
    
    def is_returned(self):
        return self.return_date is not None
    
    
    def outstanding_fine(self):
        return self.fine_amount - self.fine_paid
    
    
    def days_overdue(self):
        if self.is_overdue():
            return (timezone.now().date() - self.due_date).days
        return 0
    
    def calculate_fine(self):
        return f"${self.days_overdue() * self.DAILY_FINE_AMOUNT}"
    
    
    def mark_as_returned(self):
        if not self.is_returned():
            self.return_date = timezone.now().date()
            self.book.available_no_of_books += 1
            self.book.save()
            self.save()
        else:
            raise ValueError("This loan has already been returned.")
        

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("BOOK_CREATED", "Book Created"),
        ("LOAN_EXTENDED", "Loan Extended"),
        ("LOAN_RETURNED", "Loan Returned"),
        ("USER_REGISTERED", "User Registered"),
        ("FINE_PAID", "Fine Paid"),
    ]
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.action} by {self.user.username} on {self.timestamp}"
        
    # def get_overdue_days(self):
    #     if self.is_overdue():
    #         return (timezone.now().date() - self.due_date).days
    #     return 0
    
    # def get_fine(self):
    #     overdue_days = self.get_overdue_days()
    #     if overdue_days > 0:
    #         return overdue_days * 5  # Assuming a fine of $5 per day
    #     return 0
    
    # def get_loan_duration(self):
    #     if self.return_date:
    #         return (self.return_date - self.loan_date).days
    #     return (timezone.now().date() - self.loan_date).days       
    
    
    