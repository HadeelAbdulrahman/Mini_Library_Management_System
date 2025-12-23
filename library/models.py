from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def get_expiry():
    """Return a default expiry date for issued books (7 days from today)."""
    return timezone.now().date() + timedelta(days=7)


class StudentExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enrollment = models.CharField(max_length=40, unique=True)
    branch = models.CharField(max_length=40)

    def __str__(self) -> str:
        return f"{self.user.first_name} [{self.enrollment}]"

    @property
    def get_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def getuserid(self):
        return self.user.id


class Book(models.Model):
    CATEGORY_CHOICES = [
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('comics', 'Comics'),
        ('biography', 'Biography'),
        ('history', 'History'),
        ('novel', 'Novel'),
        ('science', 'Science'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    isbn = models.CharField(max_length=30, unique=True)
    author = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')

    def __str__(self) -> str:
        return f"{self.name} [{self.isbn}]"

    @property
    def is_available(self) -> bool:
        # Available if there is no active borrow
        return not self.borrows.filter(returned=False).exists()


class Borrow(models.Model):
    student = models.ForeignKey(StudentExtra, on_delete=models.CASCADE, related_name='borrows')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    returned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-borrowed_at']

    def mark_returned(self):
        if not self.returned:
            self.returned = True
            self.returned_at = timezone.now()
            self.save(update_fields=['returned', 'returned_at'])

    def is_overdue(self) -> bool:
        return (not self.returned) and timezone.now() > self.due_at

    def __str__(self) -> str:
        return f"{self.student.enrollment} -> {self.book.isbn}"
