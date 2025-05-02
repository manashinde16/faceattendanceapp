from django.urls import path
from attendance.views import mark_attendance, register_user, login_user
urlpatterns = [
    path('mark-attendance/', mark_attendance, name='mark_attendance'),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'), 
]
