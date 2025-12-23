from django import forms
from django.contrib.auth.models import User
from . import models
from django.db.models import Exists, OuterRef
from .models import Book, Borrow


class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500, widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))


class StudentUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']


class StudentExtraForm(forms.ModelForm):
    class Meta:
        model = models.StudentExtra
        fields = ['enrollment', 'branch']


class BookForm(forms.ModelForm):
    class Meta:
        model = models.Book
        fields = ['name', 'isbn', 'author', 'category']




class BorrowForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.none())
    seconds = forms.IntegerField(min_value=1, max_value=86400)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active = Borrow.objects.filter(book=OuterRef('pk'), returned=False)
        self.fields['book'].queryset = Book.objects.annotate(
            is_borrowed=Exists(active)
        ).filter(is_borrowed=False).order_by('name')
