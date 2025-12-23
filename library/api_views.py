from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import Book, StudentExtra, Borrow
from .serializers import BookSerializer, StudentSerializer, BorrowSerializer

@api_view(['GET', 'POST'])
def book_list(request):
    if request.method == 'GET':
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # Creation restricted to staff users
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to add books."}, status=403)

        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def book_detail(request, pk):
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BookSerializer(book)
        return Response(serializer.data)

    elif request.method == 'PUT':
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=403)
        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=403)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

from django.db import transaction

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def borrow_book(request):
    # Accept either 'book'/'book_id' and 'student'/'student_id' keys for compatibility
    book_id = request.data.get('book') or request.data.get('book_id')
    student_id = request.data.get('student') or request.data.get('student_id') or request.data.get('member')

    if not book_id or not student_id:
        return Response({"detail": "Both 'book' and 'student' are required."}, status=400)

    try:
        book = Book.objects.select_for_update().get(id=book_id)
    except Book.DoesNotExist:
        return Response({"detail": "Book not found."}, status=404)

    try:
        student = StudentExtra.objects.get(id=student_id)
    except StudentExtra.DoesNotExist:
        return Response({"detail": "Student not found."}, status=404)

    # Only allow students to borrow for themselves unless staff
    if not request.user.is_staff:
        try:
            current_student = StudentExtra.objects.get(user=request.user)
        except StudentExtra.DoesNotExist:
            return Response({"detail": "Only students can borrow books."}, status=403)
        if current_student.id != student.id:
            return Response({"detail": "You may only borrow for your own student account."}, status=403)

    # Check availability and active borrows
    if not book.is_available:
        return Response({"detail": "Book not available."}, status=409)

    if Borrow.objects.filter(book=book, student=student, returned=False).exists():
        return Response({"detail": "You already have this book borrowed and not returned."}, status=409)

    # Create borrow atomically to prevent race conditions
    with transaction.atomic():
        due_at = timezone.now() + timedelta(days=7)
        borrow = Borrow.objects.create(book=book, student=student, due_at=due_at)

    serializer = BorrowSerializer(borrow)
    return Response(serializer.data, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_book(request):
    borrow_id = request.data.get('borrow_id') or request.data.get('id')

    if not borrow_id:
        return Response({"detail": "'borrow_id' is required."}, status=400)

    try:
        borrow = Borrow.objects.get(id=borrow_id)
    except Borrow.DoesNotExist:
        return Response({"detail": "Borrow record not found."}, status=404)

    if borrow.returned:
        return Response({"detail": "This borrow is already returned."}, status=409)

    # allow staff or the borrowing student to return
    if not request.user.is_staff and borrow.student.user != request.user:
        return Response({"detail": "Permission denied."}, status=403)

    borrow.mark_returned()
    serializer = BorrowSerializer(borrow)
    return Response({"message": "Book returned.", "borrow": serializer.data}, status=200)
