"use client";

import { useEffect, useState } from "react";
import { client } from "@/client/api";

// 1. FIX: Extract the type directly as an array of items
type VendorItem = NonNullable<
  Awaited<ReturnType<typeof client.GET<"/api/analytics/vendors/">>>["data"]
>[number];

export default function VendorList() {
  const [vendors, setVendors] = useState<VendorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchVendors() {
      try {
        setLoading(true);
        const { data, error: apiError } = await client.GET("/api/analytics/vendors/");

        if (apiError) {
          throw new Error(JSON.stringify(apiError) || "Failed to fetch vendors.");
        }

        if (data) {
          // 2. FIX: data IS the array itself! Set it directly.
          setVendors(data);
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    }

    fetchVendors();
  }, []);

  // 3. UI State Render Paths
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-slate-500 font-mono text-sm">
        🔄 Querying third-party risk profiles...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm font-mono">
        ❌ Error loading pipeline state: {error}
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-bold font-mono tracking-tight text-slate-900">
          Third-Party Vendor Ledger
        </h1>
        <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-mono font-semibold">
          Count: {vendors?.length || 0}
        </span>
      </div>

      {!vendors || vendors.length === 0 ? (
        <div className="text-center p-12 bg-slate-50 border border-dashed rounded-xl text-slate-400">
          No registered vendors found. Upload an onboarding contract to begin.
        </div>
      ) : (
        <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
          <table className="w-full text-left border-collapse bg-white">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-mono font-bold text-slate-600 uppercase tracking-wider">
              <tr>
                <th className="p-4">Vendor Name</th>
                <th className="p-4">Type</th>
                <th className="p-4">Business Owner</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-sm text-slate-700 font-mono">
              {/* 3. FIX: Defensive optional chaining to guarantee safe execution */}
              {vendors?.map((vendor) => (
                <tr key={vendor.vendor_id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-4 font-semibold text-slate-900">{vendor.vendor_name}</td>
                  <td className="p-4 text-xs text-slate-500">{vendor.vendor_type}</td>
                  <td className="p-4">{vendor.business_owner}</td>
                  <td className="p-4">
                    <span
                      className={`font-bold ${
                        vendor.current_risk_score > 70
                          ? "text-red-600"
                          : vendor.current_risk_score > 40
                          ? "text-amber-600"
                          : "text-emerald-600"
                      }`}
                    >
{vendor.current_risk_score ? Number(vendor.current_risk_score).toFixed(1) : "0.0"}                    </span>
                  </td>
                  <td className="p-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium uppercase border ${
                        vendor.status === "PROCESSING"
                          ? "bg-blue-50 border-blue-200 text-blue-700 animate-pulse"
                          : vendor.status === "COMPLETED"
                          ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                          : "bg-rose-50 border-rose-200 text-rose-700"
                      }`}
                    >
                      {vendor.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}