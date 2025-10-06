from django.urls import path
from . import views

urlpatterns = [
    path('ice-arrests/', views.dashboard, name='home'),                  # Home page
    path('documentation/', views.documentation, name='documentation'),  # Documentation page
]