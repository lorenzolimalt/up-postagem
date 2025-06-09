from django.urls import path
from . import views

app_name = 'pdf_generator'

urlpatterns = [
    path('generate/', views.generate_pdf_view, name='generate_pdf'),
]