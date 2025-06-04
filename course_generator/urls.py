from django.urls import path
from . import views

app_name = 'course_generator'

urlpatterns = [
    path('generate/', views.generate_course, name='generate_course'),
]