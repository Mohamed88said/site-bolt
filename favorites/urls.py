from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('', views.FavoriteListView.as_view(), name='list'),
    path('add/<int:product_id>/', views.add_to_favorites, name='add'),
    path('remove/<int:product_id>/', views.remove_from_favorites, name='remove'),
    path('toggle/<int:product_id>/', views.toggle_favorite, name='toggle'),
]