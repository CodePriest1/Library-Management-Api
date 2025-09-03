from django.contrib import admin
from Book_app.models import Books, Loan, Genre, Library, AuditLog


# Register your models here.
admin.site.register(Books)
admin.site.register(Loan)
admin.site.register(Genre)
admin.site.register(Library)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "timestamp", "details")
    list_filter = ("action", "timestamp", "user")
    search_fields = ("details", "user__username")

