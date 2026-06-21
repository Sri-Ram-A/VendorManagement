# filepath: backend/analytics/views.py
from loguru import logger
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from core.models import Vendor


class VendorListView(APIView):
    """Returns all vendors with their current risk status and score."""

    @extend_schema(responses={200: dict})
    def get(self, request: Request) -> Response:
        logger.debug("VendorListView: fetching all vendor records.")
        vendors = Vendor.objects.all().order_by("-created_at")

        payload = [
            {
                "vendor_id": str(v.vendor_id),
                "vendor_name": v.vendor_name,
                "vendor_type": v.vendor_type,
                "business_owner": v.business_owner,
                "status": v.status,
                "current_risk_score": float(v.current_risk_score),
                "previous_risk_score": float(v.previous_risk_score),
                "created_at": v.created_at.isoformat(),
                "updated_at": v.updated_at.isoformat(),
            }
            for v in vendors
        ]

        return Response({"count": len(payload), "vendors": payload}, status=status.HTTP_200_OK)


class VendorDetailView(APIView):
    """Returns full compliance profile for a single vendor."""

    @extend_schema(responses={200: dict})
    def get(self, request: Request, vendor_id) -> Response:
        logger.debug(f"VendorDetailView: fetching vendor {vendor_id}")

        try:
            v = Vendor.objects.get(pk=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found."}, status=status.HTTP_404_NOT_FOUND)

        # Build document list
        documents = [
            {
                "document_id": str(doc.document_id),
                "document_type": doc.document_type,
                "extraction_status": doc.extraction_status,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "is_expired": doc.is_expired,
            }
            for doc in v.documents.all()
        ]

        payload = {
            "vendor_id": str(v.vendor_id),
            "vendor_name": v.vendor_name,
            "vendor_type": v.vendor_type,
            "business_owner": v.business_owner,
            "annual_spend": float(v.annual_spend) if v.annual_spend else None,
            "status": v.status,
            "current_risk_score": float(v.current_risk_score),
            "previous_risk_score": float(v.previous_risk_score),
            "risk_narrative_summary": v.risk_narrative_summary,
            "declared_data_categories": v.declared_data_categories,
            "declared_systems_accessed": v.declared_systems_accessed,
            "extracted_legal_bounds": v.extracted_legal_bounds,
            "execution_trace_log": v.execution_trace_log,
            "documents": documents,
            "created_at": v.created_at.isoformat(),
            "updated_at": v.updated_at.isoformat(),
        }

        return Response(payload, status=status.HTTP_200_OK)
    
# filepath: backend/analytics/views.py  (add to the existing file, do not touch VendorListView/VendorDetailView)
import os
import joblib
import pandas as pd
from pathlib import Path
from django.conf import settings
from loguru import logger
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from analytics.models import VendorRegistry

# ---- Load model artifacts once at module import time (not per-request) ----
ML_MODELS_DIR = Path(settings.BASE_DIR) / "analytics" / "ml_models"

_rf_model = joblib.load(ML_MODELS_DIR / "vendor_anomaly_model.pkl")
_label_encoder = joblib.load(ML_MODELS_DIR / "label_encoder.pkl")
_feature_names = joblib.load(ML_MODELS_DIR / "feature_names.pkl")


def build_features_simple(df: pd.DataFrame) -> pd.DataFrame:
    """Same feature engineering used during training - keep in sync with training script."""
    today = pd.Timestamp("today").normalize()
    out = pd.DataFrame()

    out["is_recent_breach"] = (df["breach_status"] == "Recent_Breach_12mo").astype(int)
    out["is_under_investigation"] = (df["breach_status"] == "Under_Investigation").astype(int)
    out["is_historical_breach"] = (df["breach_status"] == "Historical_Breach").astype(int)

    out["scope_high_sensitivity"] = df["data_access_scope"].isin(
        ["Customer_PII", "Financial_Data", "All_Systems"]).astype(int)
    out["scope_low_sensitivity"] = df["data_access_scope"].isin(
        ["Internal_Data", "Public_Data"]).astype(int)

    out["risk_score"] = df["risk_score"].astype(float)
    out["risk_high"] = (df["risk_score"] >= 81).astype(int)
    out["risk_elevated"] = ((df["risk_score"] >= 66) & (df["risk_score"] <= 80)).astype(int)
    out["risk_low"] = (df["risk_score"] <= 65).astype(int)

    contract_end = pd.to_datetime(df["contract_end_date"], errors="coerce")
    out["contract_days_left"] = (contract_end - today).dt.days.fillna(9999)
    out["contract_expired"] = (out["contract_days_left"] < 0).astype(int)
    out["contract_expired_severe"] = (out["contract_days_left"] < -70).astype(int)

    last_audit = pd.to_datetime(df["last_audit_date"], errors="coerce")
    out["audit_days_since"] = (today - last_audit).dt.days.fillna(9999)

    def parse_certs(cert_str):
        expired, total = 0, 0
        if pd.isna(cert_str) or cert_str == "":
            return 0, 0, 0.0
        for cert in str(cert_str).split("|"):
            if ":" in cert:
                total += 1
                try:
                    if pd.to_datetime(cert.split(":")[1].strip()) < today:
                        expired += 1
                except Exception:
                    pass
        pct = expired / total if total > 0 else 0.0
        return expired, total, pct

    parsed = df["compliance_certifications"].apply(parse_certs)
    out["expired_cert_count"] = parsed.apply(lambda x: x[0])
    out["total_cert_count"] = parsed.apply(lambda x: x[1])
    out["pct_certs_expired"] = parsed.apply(lambda x: x[2])
    out["has_expired_cert"] = (out["expired_cert_count"] > 0).astype(int)
    out["all_certs_expired"] = (
        (out["expired_cert_count"] == out["total_cert_count"]) & (out["total_cert_count"] > 0)
    ).astype(int)

    out["annual_spend"] = df["annual_spend"].astype(float)

    return out


class VendorRiskPredictionView(APIView):
    """
    Accepts a vendor_id, looks up the vendor's registry row in the DB,
    runs feature extraction + trained RandomForest model, returns the prediction.
    """

    @extend_schema(responses={200: dict})
    def get(self, request: Request, vendor_id) -> Response:
        logger.debug(f"VendorRiskPredictionView: predicting for vendor {vendor_id}")

        try:
            vendor = VendorRegistry.objects.get(pk=vendor_id)
        except VendorRegistry.DoesNotExist:
            return Response({"error": "Vendor not found in registry."}, status=status.HTTP_404_NOT_FOUND)

        vendor_dict = vendor.to_dict()
        row_df = pd.DataFrame([vendor_dict])

        X_input = build_features_simple(row_df)[_feature_names]

        pred_idx = _rf_model.predict(X_input)[0]
        pred_prob = _rf_model.predict_proba(X_input)[0]
        anomaly_type = _label_encoder.inverse_transform([pred_idx])[0]

        all_probs = {
            _label_encoder.inverse_transform([i])[0]: round(float(p), 4)
            for i, p in enumerate(pred_prob)
        }

        payload = {
            "vendor_id": vendor_dict["vendor_id"],
            "vendor_name": vendor_dict["vendor_name"],
            "is_anomaly": anomaly_type != "LOW_RISK_VENDOR",
            "anomaly_type": anomaly_type,
            "confidence": f"{pred_prob[pred_idx]:.2%}",
            "all_probs": all_probs,
        }

        return Response(payload, status=status.HTTP_200_OK)