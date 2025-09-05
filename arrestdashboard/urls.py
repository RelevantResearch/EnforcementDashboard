from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),                  # Home page
    path('documentation/', views.documentation, name='documentation'),  # Documentation page
]