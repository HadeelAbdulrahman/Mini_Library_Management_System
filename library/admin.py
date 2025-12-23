from django.contrib import admin
from .models import Book, StudentExtra, Borrow

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name','isbn','author','category')
    search_fields = ('name','isbn','author')


@admin.register(StudentExtra)
class StudentExtraAdmin(admin.ModelAdmin):
    list_display = ('user','enrollment','branch')
    search_fields = ('user__username','enrollment','user__first_name','user__last_name')


@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('student','book','borrowed_at','due_at','returned')
    list_filter = ('returned',)
    search_fields = ('student__enrollment','book__isbn','book__name')
