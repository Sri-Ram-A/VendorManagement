"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { client } from "@/lib/client";
import type { paths } from "@/types/schema";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area"; // If you use shadcn ScrollArea
// Pure Shadcn UI Component Imports
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {Button} from "@/components/ui/button";
// Icons
import { ChevronLeft, FileText, Brain, Scale, AlertCircle, RefreshCw,CheckCircle2, Clock, Terminal, Activity } from "lucide-react";

// Robust OpenAPI Schema Type Extractions
type VendorDetail = paths["/api/analytics/vendors/{vendor_id}/"]["get"]["responses"]["200"]["content"]["application/json"];
type PredictResult = paths["/api/analytics/vendors/{vendor_id}/predict/"]["get"]["responses"]["200"]["content"]["application/json"];

// Status color helpers mapped directly to Schema Enums
const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  PENDING_ASSESSMENT: { label: "Pending Assessment", className: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  PROCESSING: { label: "Processing", className: "bg-sky-500/10 text-sky-500 border-sky-500/20 animate-pulse" },
  VERIFIED_GREEN: { label: "Verified Low Risk", className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  CONDITIONAL_YELLOW: { label: "Conditional Medium", className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
  QUARANTINED_RED: { label: "Quarantined Critical", className: "bg-destructive/10 text-destructive border-destructive/20" },
};

function useVendorDetail(vendor_id: string) {
  const [vendor, setVendor] = useState<VendorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  useEffect(() => {
    if (!vendor_id) return;
    (async () => {
      const { data, error: err } = await client.GET("/api/analytics/vendors/{vendor_id}/", {
        params: { path: { vendor_id } },
      });
      if (err || !data) { setError("Vendor compliance record not resolved."); }
      else setVendor(data);
      setLoading(false);
    })();
  }, [vendor_id]);

  return { vendor, loading, error };
}
// Simple colorizer for terminal log files
function parseLogLine(line: string, index: number) {
  let colorClass = "text-muted-foreground"; // Default

  if (/error|fail|critical|exception/i.test(line)) {
    colorClass = "text-destructive font-semibold";
  } else if (/warn|alert/i.test(line)) {
    colorClass = "text-amber-500 font-semibold";
  } else if (/success|ok|pass/i.test(line)) {
    colorClass = "text-emerald-500 font-semibold";
  } else if (/info/i.test(line)) {
    colorClass = "text-sky-400";
  } else if (/trace|debug/i.test(line)) {
    colorClass = "text-muted-foreground/60";
  }

  return (
    <div key={index} className="font-mono text-[11px] leading-relaxed select-text hover:bg-muted/10 px-2 py-0.5 rounded-sm">
      <span className="text-muted-foreground/30 mr-3 inline-block w-6 text-right select-none">
        {index + 1}
      </span>
      <span className={colorClass}>{line}</span>
    </div>
  );
}



function usePrediction(vendor_id: string) {
  const [prediction, setPrediction] = useState<PredictResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!vendor_id) return;
    (async () => {
      const { data } = await client.GET("/api/analytics/vendors/{vendor_id}/predict/", {
        params: { path: { vendor_id } },
      });
      if (data) setPrediction(data);
      setLoading(false);
    })();
  }, [vendor_id]);

  return { prediction, loading };
}

export default function VendorDetailPage() {
  const params = useParams();
  const vendor_id = String(params?.vendor_id ?? "");
  const { vendor, loading, error } = useVendorDetail(vendor_id);
  const { prediction, loading: predLoading } = usePrediction(vendor_id);
  const [logContent, setLogContent] = useState<string | null>(null);
  const [fetchingLog, setFetchingLog] = useState(false);
  const [logError, setLogError] = useState<string | null>(null);
  const legalBounds = (vendor?.extracted_legal_bounds as Record<string, unknown>) ?? {};
  const dataCats = (vendor?.declared_data_categories as string[]) ?? [];
  // Parse systems accessed string into a clean array
  const systems = vendor?.declared_systems_accessed
    ? String(vendor.declared_systems_accessed).split(",").map(s => s.trim()).filter(Boolean)
    : [];
  const fetchLogFile = async (url: string) => {
    setFetchingLog(true);
    setLogError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Could not read pipeline artifact logs.");
      const text = await response.text();
      setLogContent(text);
    } catch (err: any) {
      setLogError(err.message || "Failed to stream audit file.");
    } finally {
      setFetchingLog(false);
    }
  };

  if (error) return <div className="p-6 text-destructive font-mono text-sm">❌ {error}</div>;

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Header Bar */}
      <div className="border-b border-border px-6 py-4 bg-muted/30 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="text-muted-foreground hover:text-foreground transition-colors">
            <ChevronLeft size={18} />
          </Link>
          {loading ? (
            <Skeleton className="h-5 w-48 rounded-md" />
          ) : (
            <div className="flex items-baseline gap-2">
              <h1 className="text-lg font-bold tracking-tight">{vendor?.vendor_name}</h1>
              <span className="text-xs text-muted-foreground font-mono">({vendor?.vendor_type})</span>
            </div>
          )}
        </div>
        {vendor?.status && (
          <Badge variant="outline" className={`rounded-md px-2.5 py-1 text-xs font-semibold ${STATUS_CONFIG[vendor.status]?.className || ""}`}>
            {STATUS_CONFIG[vendor.status]?.label || vendor.status}
          </Badge>
        )}
      </div>

      {/* Main Workspace Grid */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Metric Summary Rows */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-md" />)}
          </div>
        ) : (
          vendor && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <Card className="rounded-md shadow-none bg-muted/10 border-border">
                <CardContent className="p-4">
                  <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Risk Score Index</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-mono font-bold tracking-tight">
                      {vendor.current_risk_score ? Number(vendor.current_risk_score).toFixed(1) : "0.0"}
                    </span>
                    <span className="text-xs text-muted-foreground font-mono">
                      prev: {vendor.previous_risk_score ? Number(vendor.previous_risk_score).toFixed(1) : "—"}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-md shadow-none bg-muted/10 border-border">
                <CardContent className="p-4">
                  <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Annual Spend</p>
                  <div className="text-2xl font-mono font-bold tracking-tight">
                    {vendor.annual_spend ? `$${(Number(vendor.annual_spend) / 1e3).toFixed(0)}K` : "—"}
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-md shadow-none bg-muted/10 border-border">
                <CardContent className="p-4">
                  <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Business Owner</p>
                  <div className="text-base font-semibold truncate mt-1 text-foreground">
                    {vendor.business_owner}
                  </div>
                </CardContent>
              </Card>

              <Card className="rounded-md shadow-none bg-muted/10 border-border">
                <CardContent className="p-4">
                  <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Onboarding Baseline</p>
                  <div className="text-sm font-mono font-semibold mt-1">
                    {new Date(vendor.created_at).toLocaleDateString()}
                  </div>
                  <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
                    Sync: {new Date(vendor.updated_at).toLocaleTimeString()}
                  </p>
                </CardContent>
              </Card>
            </div>
          )
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Machine Learning Engine Prediction Card */}
          <Card className="rounded-md shadow-none border-border">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
              <Brain size={16} className="text-muted-foreground" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">ML Inference Telemetry</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {predLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-5 w-1/3 rounded-md" />
                  <Skeleton className="h-16 w-full rounded-md" />
                </div>
              ) : prediction && Object.keys(prediction).length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Badge variant={prediction.is_anomaly ? "destructive" : "secondary"} className="rounded-md font-mono text-[11px]">
                      {prediction.is_anomaly ? "⚠️ ANOMALOUS_SIGNATURE" : "✓ NOMINAL_COMPLIANCE"}
                    </Badge>
                    <span className="text-xs text-muted-foreground font-mono">
                      Confidence: <span className="text-foreground font-bold">{String(prediction.confidence ?? "—")}</span>
                    </span>
                  </div>
                  {prediction.all_probs && (
                    <div className="space-y-2.5 pt-2">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                        Classification Probability Density
                      </p>
                      {Object.entries(prediction.all_probs as Record<string, number>)
                        .sort(([, a], [, b]) => b - a)
                        .map(([cls, prob]: [string, number]) => ( // 👈 Explicitly type the tuple here
                          <div key={cls} className="space-y-1">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-muted-foreground capitalize">
                                {cls.replace(/_/g, " ")}
                              </span>
                              <span className="text-foreground font-semibold">
                                {(prob * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-1.5 bg-secondary rounded-none overflow-hidden">
                              <div className="h-full bg-primary" style={{ width: `${prob * 100}%` }} />
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground font-mono">Inference logs not generated for target pipeline.</p>
              )}
            </CardContent>
          </Card>

          {/* AI Risk Narrative Card */}
          <Card className="rounded-md shadow-none border-border">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
              <AlertCircle size={16} className="text-muted-foreground" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">AI Narrative Summary</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full rounded-md" />
                  <Skeleton className="h-4 w-[85%] rounded-md" />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed font-sans">
                  {typeof vendor?.risk_narrative_summary === "string"
                    ? vendor.risk_narrative_summary
                    : "No risk narrative generated yet. Document extraction must complete before pipeline processing begins."}
                </p>
              )}
            </CardContent>
          </Card>
          {/* Contract Obligations Layout */}
          <Card className="rounded-md shadow-none border-border lg:col-span-2">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
              <Scale size={16} className="text-muted-foreground" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Extracted Contract Obligations
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {loading ? (
                <Skeleton className="h-32 w-full rounded-md" />
              ) : Object.keys(legalBounds).length === 0 ? (
                <p className="text-xs text-muted-foreground font-mono py-4">
                  No active obligations parsed. Upload corporate records below to invoke pipeline parsing analysis.
                </p>
              ) : (
                <dl className="grid grid-cols-1 sm:grid-cols-3 gap-x-8 gap-y-4">
                  {Object.entries(legalBounds)
                    .filter(([key]) => key !== "subprocessors_disclosed") // Kept in separate dedicated side-panel
                    .map(([key, val]) => {
                      // 1. Resolve hidden or nested "[object Object]" instances
                      let cleanVal: any = val;
                      if (typeof val === "object" && val !== null) {
                        // Unpack typical nested field properties like { value: ... } or { display: ... } if generated by the backend
                        cleanVal = (val as any).value ?? (val as any).display ?? JSON.stringify(val);
                      }

                      // 2. Parse out text if it arrives as an unparsed raw stringified JSON primitive
                      if (typeof cleanVal === "string" && (cleanVal.startsWith("{") || cleanVal.startsWith("["))) {
                        try {
                          const parsed = JSON.parse(cleanVal);
                          cleanVal = parsed.value ?? parsed;
                        } catch (e) {
                          // Keep original string if fallback parsing errors out
                        }
                      }

                      // 3. Set up validation rendering paths
                      let display = "—";
                      const isBoolean = typeof cleanVal === "boolean" || cleanVal === "true" || cleanVal === "false";

                      if (isBoolean) {
                        display = cleanVal === true || cleanVal === "true" ? "True" : "False";
                      } else if (Array.isArray(cleanVal)) {
                        display = cleanVal.join(", ");
                      } else if (cleanVal !== undefined && cleanVal !== null) {
                        display = String(cleanVal);
                      }

                      // 4. Clean up timestamp variables safely
                      const isDateKey = key.includes("date") || key.includes("end");
                      if (isDateKey && display !== "—") {
                        const parsedDate = Date.parse(display);
                        if (!isNaN(parsedDate)) {
                          display = new Date(parsedDate).toLocaleDateString();
                        } else {
                          // Try falling back to raw value if parse fails to prevent "Invalid Date" output string crashes
                          display = String(cleanVal);
                        }
                      }

                      // 5. Highlight structural system anomalies
                      const isWarning =
                        (key === "liability_uncapped_for_security_breach" && (cleanVal === true || cleanVal === "true")) ||
                        (key === "soc2_opinion_type" && String(cleanVal).toLowerCase() === "qualified");

                      return (
                        <div key={key} className="border-b border-border pb-2">
                          <dt className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider truncate" title={key}>
                            {key.replace(/_/g, " ")}
                          </dt>
                          <dd className={`text-sm font-mono mt-1 font-semibold tracking-tight ${isWarning ? "text-destructive" : "text-foreground"}`}>
                            {display}
                            {key.includes("hours") && display !== "—" && " hrs"}
                            {key.includes("days") && display !== "—" && " days"}
                            {key.includes("usd") && display !== "—" && !display.startsWith("$") && " USD"}
                          </dd>
                        </div>
                      );
                    })}
                </dl>
              )}
            </CardContent>
          </Card>

          {/* Scope Access Data Categories */}
          <Card className="rounded-md shadow-none border-border">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
              <Activity size={16} className="text-muted-foreground" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Declared Data & Network Boundaries</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-4">
              <div className="space-y-1.5">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Asset Classes Exchanged</p>
                {dataCats.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {dataCats.map(cat => (
                      <Badge key={cat} variant={["PCI_CARDHOLDER_DATA", "CREDENTIALS_AUTH"].includes(cat) ? "destructive" : "secondary"} className="rounded-md font-mono text-[10px]">
                        {cat}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground font-mono">No explicitly cataloged operational categories.</p>
                )}
              </div>

              <div className="pt-2 space-y-1.5">
                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Logical Integration Boundaries</p>
                {systems.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {systems.map(s => (
                      <span key={s} className="px-2 py-0.5 font-mono text-xs bg-muted border border-border text-muted-foreground rounded-md">
                        {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground font-mono">No connection logical networks declared.</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Subprocessors Panel */}
          <Card className="rounded-md shadow-none border-border">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
              <Clock size={16} className="text-muted-foreground" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Downstream Corporate Subprocessors</CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              {((legalBounds["subprocessors_disclosed"] as string[]) ?? []).length ? (
                <div className="flex flex-wrap gap-1.5">
                  {((legalBounds["subprocessors_disclosed"] as string[]) ?? []).map(sp => (
                    <Badge key={sp} variant="outline" className="rounded-md font-mono text-[11px] text-foreground bg-muted/40">
                      {sp}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground font-mono">No nested down-line third parties disclosed in contract definitions.</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Document Vault Secure Ledger */}
        <Card className="rounded-md shadow-none border-border">
          <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-3 border-b bg-muted/10">
            <FileText size={16} className="text-muted-foreground" />
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Secured Document Vault</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-4"><Skeleton className="h-16 w-full rounded-md" /></div>
            ) : vendor?.documents && vendor.documents.length > 0 ? (
              <Table>
                <TableHeader className="bg-muted/30 font-mono text-[11px]">
                  <TableRow className="hover:bg-transparent border-b">
                    <TableHead className="pl-6 h-10">Document Identifier</TableHead>
                    <TableHead className="h-10">Type Definition</TableHead>
                    <TableHead className="h-10">Validation Status</TableHead>
                    <TableHead className="h-10">Pipeline Status</TableHead>
                    <TableHead className="pr-6 h-10 text-right">Uploaded Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="font-mono text-xs">
                  {vendor.documents.map((doc) => (
                    <TableRow key={doc.document_id} className="hover:bg-muted/20 border-b last:border-0">
                      <TableCell className="pl-6 py-3 font-semibold text-foreground">
                        <div className="flex items-center gap-2">
                          <FileText size={13} className="text-muted-foreground" />
                          <span>{doc.document_id}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-sans font-semibold">{doc.document_type}</TableCell>
                      <TableCell>
                        {doc.is_expired ? (
                          <Badge variant="destructive" className="rounded-md font-sans text-[10px] py-0 px-1.5">Expired</Badge>
                        ) : (
                          <Badge variant="secondary" className="rounded-md font-sans text-[10px] py-0 px-1.5 bg-emerald-500/10 text-emerald-500 border-emerald-500/20">Active</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className={`text-[11px] font-bold ${doc.extraction_status === "SUCCESS" ? "text-emerald-500" : doc.extraction_status === "FAILED" ? "text-destructive" : "text-sky-500"}`}>
                          ● {doc.extraction_status}
                        </span>
                      </TableCell>
                      <TableCell className="pr-6 text-right text-muted-foreground">
                        {new Date(doc.uploaded_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="text-xs text-muted-foreground font-mono p-6 text-center">No structural documents mapped onto this security record profile.</p>
            )}
          </CardContent>
        </Card>

        {/* Audit Trace Logs Component */}
        {vendor?.execution_trace_log && (
          <Card className="rounded-md shadow-none border-border bg-muted/20">
            <CardContent className="px-4 py-3 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Terminal size={14} />
                <span>Active Pipeline Trace Reference</span>
              </div>

              <Dialog onOpenChange={(open) => open && fetchLogFile(vendor.execution_trace_log!)}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="h-7 text-xs font-sans rounded-md bg-background shadow-none border-border hover:bg-muted">
                    Inspect System Logs
                  </Button>
                </DialogTrigger>

                <DialogContent className="max-w-4xl max-h-[80vh] rounded-md flex flex-col p-6 border-border bg-[#0D1117] text-slate-100">
                  <DialogHeader className="border-b border-slate-800 pb-3">
                    <DialogTitle className="text-sm font-bold tracking-tight text-slate-200 flex items-center gap-2 font-mono">
                      <Terminal size={16} className="text-sky-400" />
                      {vendor.execution_trace_log.split("/").pop() || "execution_trace.log"}
                    </DialogTitle>
                    <DialogDescription className="text-xs text-slate-400 font-sans">
                      Asynchronous runtime execution trace mapped onto pipeline task loops.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="flex-1 min-h-0 bg-[#090D12] border border-slate-800 rounded-md p-4 overflow-hidden mt-4">
                    {fetchingLog && (
                      <div className="h-64 flex flex-col items-center justify-center gap-2 font-mono text-xs text-slate-500">
                        <RefreshCw size={16} className="animate-spin text-sky-500" />
                        <span>Streaming remote log data bytes...</span>
                      </div>
                    )}

                    {logError && (
                      <div className="h-64 flex items-center justify-center font-mono text-xs text-destructive">
                        ❌ {logError}
                      </div>
                    )}

                    {!fetchingLog && !logError && logContent !== null && (
                      <ScrollArea className="h-[50vh] pr-2">
                        <div className="font-mono text-xs selection:bg-sky-500/30 whitespace-pre-wrap selection:text-white">
                          {logContent.trim() ? (
                            logContent.split("\n").map((line, idx) => parseLogLine(line, idx))
                          ) : (
                            <span className="text-slate-600 italic">Target execution file trace buffer is empty.</span>
                          )}
                        </div>
                      </ScrollArea>
                    )}
                  </div>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}