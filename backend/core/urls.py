from django.urls import path
from .views import VendorIngestionView

urlpatterns = [
    path(
        "vendors/ingest",
        VendorIngestionView.as_view(),
        name="vendor-ingestion-gateway",
    ),
]
