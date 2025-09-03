from rest_framework import serializers
from Book_app.models import Books, Loan, AuditLog, Genre, Library
from django.contrib.auth.models import User

# class BookSerializer(serializers.ModelSerializer): 
#     available_no_of_books =  serializers.ReadOnlyField()  # Read-only field for available copies
    
#     class Meta:
#         model = Books
#         fields = [
#             'id', 'title', 'author', 'isbn', 'publication_year',
#             'genre', 'total_no_of_books', 'available_no_of_books' 
#         ]
#         read_only_fields = ['isbn']  # Assuming ISBN should not be modified after creation
    

# class BookSerializer(serializers.ModelSerializer):
#     # override genres to accept both IDs and names
#     genre = serializers.SlugRelatedField(
#         many=True,
#         slug_field='name',
#         queryset=Genre.objects.all()
#     )

#     class Meta:
#         model = Books
#         fields = '__all__'

#     def create(self, validated_data):
#         genres_data = validated_data.pop('genres', [])
#         book = Books.objects.create(**validated_data)
#         for genre in genres_data:
#             genre_obj, _ = Genre.objects.get_or_create(name=genre.name)
#             book.genres.add(genre_obj)
#         return book

class BookSerializer(serializers.ModelSerializer):
    # genre = serializers.SlugRelatedField(
    #     many=True,
    #     slug_field='name',
    #     queryset=Genre.objects.all()
    # )
    # library = serializers.CharField()  # accept library name directly
    genres = serializers.SerializerMethodField(read_only=True)  # for GET
    genre = serializers.ListField(                             # for POST/PUT/PATCH
        child=serializers.CharField(),
        write_only=True,
        required=False
    )
    library = serializers.CharField()

    class Meta:
        model = Books
        fields = '__all__'

    def get_genres(self, obj):
        return [g.name for g in obj.genre.all()]

    def create(self, validated_data):
        genres_data = validated_data.pop('genre', [])
        library_name = validated_data.pop('library')

        # Get or create the library
        library_obj, _ = Library.objects.get_or_create(name=library_name)

        # Create the book
        book = Books.objects.create(library=library_obj, **validated_data)

        # Attach genres
        for genre_name in genres_data:
            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
            book.genre.add(genre_obj)

        return book

    def update(self, instance, validated_data):
        genres_data = validated_data.pop('genre', None)
        library_name = validated_data.pop('library', None)

        # Update library if provided
        if library_name:
            library_obj, _ = Library.objects.get_or_create(name=library_name)
            instance.library = library_obj

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update genres if provided
        if genres_data is not None:
            instance.genre.clear()  # remove old ones
            for genre_name in genres_data:
                genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                instance.genre.add(genre_obj)

        instance.save()
        return instance
    # def get_available_copies(self, obj):
    #     return obj.available_copies

class UserFineSummarySerializer(serializers.Serializer):
    total_fines = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2)


class userSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}  # Password should not be read
        
class LoanSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Display username instead of ID
    book_title = serializers.StringRelatedField(source='book.title', read_only=True) # Display book title instead of ID
    book = serializers.PrimaryKeyRelatedField(queryset=Books.objects.all())
    is_overdue = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    fine_amount = serializers.SerializerMethodField()
   
    class Meta:
        model = Loan
        fields = '__all__'
        # ['id', 'user', 'book', 'book_title', 'loan_date', 'due_date', 'return_date', 'returned','is_overdue', 'days_overdue', 'calculate_fine']
        read_only_fields = ['user', 'loan_date', 'due_date', 'return_date']  # Assuming loan date is set automatically and should not be modified
        
    def get_is_overdue(self, obj):
        return obj.is_overdue()    
    
    def get_days_overdue(self, obj):
        return obj.days_overdue()
    
    def get_fine_amount(self, obj):
        return obj.calculate_fine()
   
   
class BulkBookUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    
class BulkLoanActionSerializer(serializers.Serializer):
    loan_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    action = serializers.ChoiceField(choices=["return", "extend"])
    extension_days = serializers.IntegerField(required=False, min_value=1)
    
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
    # action = serializers.ChoiceField(choices=["return", "extend"]) --- IGNORE ---
    # extension_days = serializers.IntegerField(required=False, min_value=1) --- IGNORE
    

class FlexibleGenreField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        # If ID (int or str digit) → normal handling
        if isinstance(data, int) or (isinstance(data, str) and data.isdigit()):
            return super().to_internal_value(data)

        # If name → lookup by string
        try:
            return Genre.objects.get(name=data)
        except Genre.DoesNotExist:
            raise serializers.ValidationError(f"Genre '{data}' does not exist.")


# class BookSerializer(serializers.ModelSerializer):
#     genre = FlexibleGenreField(
#         queryset=Genre.objects.all(),
#         many=True   # ✅ allow multiple
#     )

#     class Meta:
#         model = Books
#         fields = '__all__'

