from django.contrib import admin
from django.urls import path , include
from django.contrib.auth import views as auth_views
from library import views, api_views

# Use our custom logout view (accepts GET and POST to avoid 405 on GET)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home_view, name='home'),
    path('studentclick', views.studentclick_view, name='studentclick'),
    path('adminclick', views.adminclick_view, name='adminclick'),

    # Students
    path('studentsignup', views.studentsignup_view, name='studentsignup'),
    path('studentlogin', auth_views.LoginView.as_view(template_name='library/studentlogin.html'), name='studentlogin'),

    path('logout', views.logout_view, name='logout'),
    path('afterlogin', views.afterlogin_view, name='afterlogin'),

    # Dashboards
    path('admin-afterlogin', views.admin_afterlogin_view, name='admin-afterlogin'),
    path('student-afterlogin', views.student_afterlogin_view, name='student-afterlogin'),

    # Admin: books CRUD (site UI)
    path('addbook', views.addbook_view, name='addbook'),
    path('viewbook', views.viewbook_view, name='viewbook'),
    path('books/<int:pk>/edit', views.updatebook_view, name='updatebook'),
    path('books/<int:pk>/delete', views.deletebook_view, name='deletebook'),

    # Admin: borrowed list
    path('borrowedbooks', views.borrowedbooks_view, name='borrowedbooks'),

    # Student: browse/borrow
    path('books', views.books_view, name='books'),
    path('borrow', views.borrow_view, name='borrow'),
    path('myborrows', views.myborrows_view, name='myborrows'),
    path('borrow/<int:borrow_id>/return', views.return_borrow_view, name='returnborrow'),

    path('contactus', views.contactus_view, name='contactus'),

    # API endpoints
    path('api/books/', api_views.book_list),
    path('api/books/<int:pk>/', api_views.book_detail),

    path('api/borrow/', api_views.borrow_book),
    path('api/return/', api_views.return_book),

    path('', include('library.urls')),
]
