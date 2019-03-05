from django.urls import path

from . import views

urlpatterns = [
    path('', views.listings, name='listings'),
    # following will look like /listings/1 or index of specific listing
    path('<int:listing_id>', views.listing, name='listing'),
    path('edit/<int:listing_id>', views.edit, name='edit'),
    path('create', views.create, name='create'),
    path('delete/<int:listing_id>', views.delete, name='delete'),
]
