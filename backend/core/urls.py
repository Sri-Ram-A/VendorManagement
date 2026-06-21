from django.urls import path
from . import views

urlpatterns = [
    path(
        "vendors/ingest",
        views.VendorDocumentIngestionView.as_view(),
        name="vendor-ingestion-gateway",
    ),
]
