from django.urls import path
from . import views

app_name = 'returns'

urlpatterns = [
    path('', views.ReturnRequestListView.as_view(), name='list'),
    path('<int:pk>/', views.ReturnRequestDetailView.as_view(), name='detail'),
    path('create/<uuid:order_id>/', views.create_return_request, name='create'),
    path('<int:pk>/cancel/', views.cancel_return_request, name='cancel'),
]