from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),
    path('conditions/', views.conditions, name='conditions'),
    path('politique-retour/', views.politique_retour, name='politique_retour'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),  # Ajouté
]