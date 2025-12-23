from rest_framework import serializers
from .models import Book, StudentExtra, Borrow

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentExtra
        fields = '__all__'

class BorrowSerializer(serializers.ModelSerializer):
    # Nested read-only representation
    book = BookSerializer(read_only=True)
    student = StudentSerializer(read_only=True)

    # Write-only fields to accept IDs on create/update
    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book', write_only=True, required=True)
    student_id = serializers.PrimaryKeyRelatedField(queryset=StudentExtra.objects.all(), source='student', write_only=True, required=True)

    class Meta:
        model = Borrow
        fields = ['id', 'borrowed_at', 'due_at', 'returned_at', 'returned', 'student', 'book', 'book_id', 'student_id']
        read_only_fields = ['id', 'borrowed_at', 'returned_at', 'returned', 'student', 'book']
