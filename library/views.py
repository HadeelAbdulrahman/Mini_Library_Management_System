from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from . import forms, models
from .models import Borrow, Book


def logout_view(request):
    """Log the user out and redirect to home. Accepts GET and POST to avoid 405 on quick clicks."""
    # Allow either GET or POST to avoid Method Not Allowed when users click anchor links
    auth_logout(request)
    return redirect('home')


def is_admin(user):
    return user.is_authenticated and user.is_staff


def is_student(user):
    return user.is_authenticated and user.groups.filter(name='STUDENT').exists()


def home_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'library/index.html')


def studentclick_view(request):
    """Show the student entry page. If the user is authenticated and is a student
    redirect them to their dashboard; otherwise render the student panel so other
    users (including admins) can still reach the student-login/landing page."""
    if request.user.is_authenticated:
        if is_student(request.user):
            return redirect('afterlogin')
        # authenticated but not a student -> render student panel so they can choose/login
    return render(request, 'library/studentclick.html')


def adminclick_view(request):
    """Show admin entry or redirect admins to their dashboard. Non-admins see
    the admin login page (or are redirected into Django admin if desired)."""
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin-afterlogin')
        # authenticated but not admin -> show admin login panel
    # Admin signup removed — admins use /admin/ only
    return redirect('/admin/')


def studentsignup_view(request):
    userForm = forms.StudentUserForm()
    extraForm = forms.StudentExtraForm()

    if request.method == 'POST':
        userForm = forms.StudentUserForm(request.POST)
        extraForm = forms.StudentExtraForm(request.POST)

        if userForm.is_valid() and extraForm.is_valid():
            user = userForm.save(commit=False)
            user.set_password(user.password)
            user.save()

            student_group, _ = Group.objects.get_or_create(name='STUDENT')
            student_group.user_set.add(user)

            extra = extraForm.save(commit=False)
            extra.user = user
            extra.save()

            messages.success(request, "Student account created. Please login.")
            return redirect('studentlogin')

    return render(request, 'library/studentsignup.html', {'form1': userForm, 'form2': extraForm})


@login_required
def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-afterlogin')
    if is_student(request.user):
        return redirect('student-afterlogin')

    # If the authenticated user is neither admin nor student, log them out
    # and show a helpful message so they don't get silently redirected back to login.
    messages.error(request, "Your account is not assigned the STUDENT role. Please contact an administrator.")
    auth_logout(request)
    return redirect('studentlogin')


# -----------------------------
# Admin dashboard (site UI)
# -----------------------------
@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def admin_afterlogin_view(request):
    return render(request, 'library/adminafterlogin.html')


@login_required(login_url='/studentlogin')
@user_passes_test(is_student, login_url='/studentlogin')
def student_afterlogin_view(request):
    return render(request, 'library/studentafterlogin.html')


# -----------------------------
# Admin: Books CRUD (site UI)
# -----------------------------
@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def addbook_view(request):
    form = forms.BookForm()
    if request.method == 'POST':
        form = forms.BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Book added.")
            return redirect('viewbook')
    return render(request, 'library/addbook.html', {'form': form})


@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def viewbook_view(request):
    books = Book.objects.all().order_by('name')
    return render(request, 'library/viewbook.html', {'books': books, 'admin_mode': True})


@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def updatebook_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = forms.BookForm(instance=book)
    if request.method == 'POST':
        form = forms.BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated.")
            return redirect('viewbook')
    return render(request, 'library/editbook.html', {'form': form, 'book': book})


@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def deletebook_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Book deleted.")
        return redirect('viewbook')
    return render(request, 'library/deletebook.html', {'book': book})


@login_required(login_url='/admin/')
@user_passes_test(is_admin, login_url='/admin/')
def borrowedbooks_view(request):
    borrows = Borrow.objects.select_related('book', 'student', 'student__user').order_by('-borrowed_at')
    return render(request, 'library/borrowedbooks.html', {'borrows': borrows})


# -----------------------------
# Student: Available books only
# -----------------------------
@login_required(login_url='/studentlogin')
@user_passes_test(is_student, login_url='/studentlogin')
def books_view(request):
    active_ids = Borrow.objects.filter(returned=False).values_list('book_id', flat=True)
    books = Book.objects.exclude(id__in=active_ids).order_by('name')
    return render(request, 'library/books.html', {'books': books})


@login_required(login_url='/studentlogin')
@user_passes_test(is_student, login_url='/studentlogin')
def borrow_view(request):
    form = forms.BorrowForm()

    if request.method == 'POST':
        form = forms.BorrowForm(request.POST)
        if form.is_valid():
            book = form.cleaned_data['book']
            seconds = form.cleaned_data['seconds']

            # Server-side check (important)
            already_borrowed = Borrow.objects.filter(book=book, returned=False).exists()
            if already_borrowed:
                messages.error(request, "This book is currently unavailable.")
                return redirect('borrow')

            student = get_object_or_404(models.StudentExtra, user=request.user)
            due_at = timezone.now() + timedelta(seconds=seconds)

            borrow = Borrow.objects.create(student=student, book=book, due_at=due_at)

            remaining_ms = max(0, int((borrow.due_at - timezone.now()).total_seconds() * 1000))
            return render(request, 'library/borrowsuccess.html', {
                'borrow': borrow,
                'remaining_ms': remaining_ms
            })

    return render(request, 'library/borrow.html', {'form': form})


@login_required(login_url='/studentlogin')
@user_passes_test(is_student, login_url='/studentlogin')
def myborrows_view(request):
    student = get_object_or_404(models.StudentExtra, user=request.user)
    borrows = Borrow.objects.filter(student=student).select_related('book').order_by('-borrowed_at')
    return render(request, 'library/myborrows.html', {'borrows': borrows})


@login_required(login_url='/studentlogin')
@user_passes_test(is_student, login_url='/studentlogin')
def return_borrow_view(request, borrow_id):
    student = get_object_or_404(models.StudentExtra, user=request.user)
    borrow = get_object_or_404(Borrow, id=borrow_id, student=student)
    borrow.mark_returned()
    return JsonResponse({'ok': True})


def contactus_view(request):
    form = forms.ContactusForm()
    if request.method == 'POST':
        form = forms.ContactusForm(request.POST)
        if form.is_valid():
            messages.success(request, "Thanks! We received your message.")
            return redirect('contactus')
    return render(request, 'library/contactus.html', {'form': form})
