# filepath: backend/analytics/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("vendors/", views.VendorListView.as_view(), name="vendor-list"),
    path("vendors/<uuid:vendor_id>/", views.VendorDetailView.as_view(), name="vendor-detail"),
]