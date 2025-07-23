from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('category/<slug:slug>/', views.CategoryListView.as_view(), name='category'),
    path('seller/products/', views.SellerProductListView.as_view(), name='seller_products'),
    path('seller/products/add/', views.ProductCreateView.as_view(), name='add_product'),
    path('seller/products/<slug:slug>/edit/', views.ProductUpdateView.as_view(), name='edit_product'),
    path('seller/products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='delete_product'),
    path('product/<slug:slug>/review/', views.add_review, name='add_review'),
]