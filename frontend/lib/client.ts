import createClient from "openapi-fetch";
import type { paths } from "@/types/schema";

export const client = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

// ── Type helpers derived directly from the schema ──────────────────────────
type GET<P extends keyof paths> = paths[P] extends { get: infer G } ? G : never;
type OkResponse<G> = G extends { responses: { 200: { content: { "application/json": infer T } } } } ? T : never;

export type VendorList   = OkResponse<GET<"/api/analytics/vendors/">>[number];
export type VendorDetail = OkResponse<GET<"/api/analytics/vendors/{vendor_id}/">>;
export type PredictResult = OkResponse<GET<"/api/analytics/vendors/{vendor_id}/predict/">>;
