"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { client } from "@/lib/client";
import type { paths } from "@/types/schema";
import { ThemeToggle } from "@/components/theme-toggle";

// Pure Shadcn UI Component Imports
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

// Icons
import { RefreshCw, ChevronRight, TrendingUp, TrendingDown, Minus, AlertTriangle, ShieldAlert } from "lucide-react";

// Robust OpenAPI Schema Type Extractions
type VendorList = paths["/api/analytics/vendors/"]["get"]["responses"]["200"]["content"]["application/json"][number];

// Schema Enum Status Mapping Configuration
const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  PENDING_ASSESSMENT: { label: "Pending Assessment", className: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  PROCESSING: { label: "Processing", className: "bg-sky-500/10 text-sky-500 border-sky-500/20 animate-pulse" },
  VERIFIED_GREEN: { label: "Verified Low Risk", className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  CONDITIONAL_YELLOW: { label: "Conditional Medium", className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20" },
  QUARANTINED_RED: { label: "Quarantined Critical", className: "bg-destructive/10 text-destructive border-destructive/20" },
};

// ── Hooks & Operational Core Logic ───────────────────────────────────────────
function useVendors() {
  const [vendors, setVendors] = useState<VendorList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);

  async function load() {
    setLoading(true);
    const { data, error: err } = await client.GET("/api/analytics/vendors/");
    if (err || !data) { 
      setError("Could not connect to the vendor risk API engine."); 
      setLoading(false); 
      return; 
    }
    setVendors(data);
    setRefreshedAt(new Date());
    setLoading(false);
  }

  useEffect(() => { load(); }, []);
  return { vendors, loading, error, refreshedAt, reload: load };
}

function deriveStats(vendors: VendorList[]) {
  const total    = vendors.length;
  const red      = vendors.filter(v => v.status === "QUARANTINED_RED").length;
  const yellow   = vendors.filter(v => v.status === "CONDITIONAL_YELLOW").length;
  const green    = vendors.filter(v => v.status === "VERIFIED_GREEN").length;
  const pending  = vendors.filter(v => v.status === "PENDING_ASSESSMENT" || v.status === "PROCESSING").length;
  const avgScore = total
    ? vendors.reduce((acc, v) => acc + parseFloat(v.current_risk_score ?? "0"), 0) / total
    : 0;
  return { total, red, yellow, green, pending, avgScore };
}

// ── Score Trend Sub-Component ────────────────────────────────────────────────
function ScoreTrend({ current, previous }: { current: string; previous: string }) {
  const delta = parseFloat(current) - parseFloat(previous);
  if (Math.abs(delta) < 0.5) return <Minus size={12} className="text-muted-foreground" />;
  if (delta > 0) return <TrendingUp size={12} className="text-destructive" />;
  return <TrendingDown size={12} className="text-emerald-500" />;
}

// ── Main Page Layout Component ────────────────────────────────────────────────
export default function DashboardPage() {
  const { vendors, loading, error, refreshedAt, reload } = useVendors();
  const stats = deriveStats(vendors);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const filtered = vendors
    .filter(v => !search || v.vendor_name.toLowerCase().includes(search.toLowerCase()) ||
                            v.vendor_type.toLowerCase().includes(search.toLowerCase()))
    .filter(v => statusFilter === "ALL" || v.status === statusFilter)
    .sort((a, b) => parseFloat(b.current_risk_score ?? "0") - parseFloat(a.current_risk_score ?? "0"));

  const criticals = vendors.filter(v => v.status === "QUARANTINED_RED");

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Universal Workspace Header */}
      <div className="border-b border-border px-6 py-4 flex items-center justify-between bg-muted/30">
        <div>
          <h1 className="text-base font-bold tracking-tight">Portfolio Overview</h1>
          {refreshedAt && (
            <p className="text-[11px] text-muted-foreground font-mono">
              Last pipeline sync: {refreshedAt.toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button
            variant="outline"
            size="sm"
            onClick={reload}
            disabled={loading}
            className="rounded-md text-xs font-mono"
          >
            <RefreshCw size={12} className={`mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Sync
          </Button>
        </div>
      </div>

      {/* Threat Bar Alerts */}
      {criticals.length > 0 && (
        <Alert variant="destructive" className="rounded-none border-x-0 border-t-0 border-b bg-destructive/10 text-destructive px-6 py-3 flex items-center gap-3 space-y-0">
          <ShieldAlert className="h-4 w-4 shrink-0 text-destructive" />
          <div className="text-sm">
            <span className="font-bold">{criticals.length} Vendor Pipeline Containment Faults: </span>
            <span className="opacity-90">{criticals.map(v => v.vendor_name).join(", ")}</span>
          </div>
          <span className="ml-auto hidden md:inline text-[10px] font-mono uppercase tracking-wider font-semibold opacity-70">
            Immediate Quarantine Enforcement Required
          </span>
        </Alert>
      )}

      {/* Content Canvas */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {error && (
          <Alert variant="destructive" className="rounded-md">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Network Resolution Fault</AlertTitle>
            <AlertDescription className="font-mono text-xs">{error}</AlertDescription>
          </Alert>
        )}

        {/* Aggregated Portfolio Statistic Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="rounded-md shadow-none bg-muted/10 border-border">
            <CardContent className="p-4">
              <p className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Total Portfolio</p>
              <div className="text-2xl font-mono font-bold tracking-tight">{stats.total}</div>
            </CardContent>
          </Card>

          <Card className="rounded-md shadow-none bg-muted/10 border-border border-destructive/20 bg-destructive/5">
            <CardContent className="p-4">
              <p className="text-[11px] font-bold text-destructive uppercase tracking-wider mb-1">Critical Risk</p>
              <div className="text-2xl font-mono font-bold tracking-tight text-destructive">{stats.red}</div>
            </CardContent>
          </Card>

          <Card className="rounded-md shadow-none bg-muted/10 border-border border-yellow-500/20 bg-yellow-500/5">
            <CardContent className="p-4">
              <p className="text-[11px] font-bold text-yellow-600 dark:text-yellow-500 uppercase tracking-wider mb-1">Medium Risk</p>
              <div className="text-2xl font-mono font-bold tracking-tight text-yellow-600 dark:text-yellow-500">{stats.yellow}</div>
            </CardContent>
          </Card>

          <Card className="rounded-md shadow-none bg-muted/10 border-border border-emerald-500/20 bg-emerald-500/5">
            <CardContent className="p-4">
              <p className="text-[11px] font-bold text-emerald-500 uppercase tracking-wider mb-1">Low Risk</p>
              <div className="text-2xl font-mono font-bold tracking-tight text-emerald-500">{stats.green}</div>
            </CardContent>
          </Card>

          <Card className="rounded-md shadow-none bg-muted/10 border-border border-sky-500/20 bg-sky-500/5">
            <CardContent className="p-4">
              <p className="text-[11px] font-bold text-sky-500 uppercase tracking-wider mb-1">In Processing</p>
              <div className="text-2xl font-mono font-bold tracking-tight text-sky-500">{stats.pending}</div>
            </CardContent>
          </Card>

          <Card className={`rounded-md shadow-none border-border ${
            stats.avgScore >= 66 ? "bg-destructive/5 border-destructive/20" : stats.avgScore >= 40 ? "bg-yellow-500/5 border-yellow-500/20" : "bg-emerald-500/5 border-emerald-500/20"
          }`}>
            <CardContent className="p-4">
              <p className={`text-[11px] font-bold uppercase tracking-wider mb-1 ${
                stats.avgScore >= 66 ? "text-destructive" : stats.avgScore >= 40 ? "text-yellow-600 dark:text-yellow-500" : "text-emerald-500"
              }`}>Avg Portfolio Risk</p>
              <div className={`text-2xl font-mono font-bold tracking-tight ${
                stats.avgScore >= 66 ? "text-destructive" : stats.avgScore >= 40 ? "text-yellow-600 dark:text-yellow-500" : "text-emerald-500"
              }`}>{stats.avgScore.toFixed(1)}</div>
            </CardContent>
          </Card>
        </div>

        {/* Unified Risk Distribution Composite Line */}
        <Card className="rounded-md shadow-none bg-muted/10 border-border">
          <CardContent className="p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Risk Allocation Index</span>
              <div className="flex items-center gap-4 normal-case tracking-normal">
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-destructive inline-block rounded-sm" />Critical</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-amber-500 inline-block rounded-sm" />Medium</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-emerald-500 inline-block rounded-sm" />Low</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 bg-sky-500 inline-block rounded-sm" />Pending</span>
              </div>
            </div>
            
            {/* Structural Bar Component Breakdown */}
            <div className="flex h-2.5 w-full bg-secondary rounded-sm overflow-hidden">
              {stats.total > 0 && (
                <>
                  <div style={{ width: `${(stats.red / stats.total) * 100}%` }} className="bg-destructive" />
                  <div style={{ width: `${(stats.yellow / stats.total) * 100}%` }} className="bg-amber-500" />
                  <div style={{ width: `${(stats.pending / stats.total) * 100}%` }} className="bg-sky-500" />
                  <div style={{ width: `${(stats.green / stats.total) * 100}%` }} className="bg-emerald-500" />
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Filter Layout Controller Tool Bar */}
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
          <div className="flex flex-1 w-full sm:w-auto max-w-sm items-center gap-2">
            <Input
              type="text"
              placeholder="Filter ledger indices..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="bg-card border-border rounded-md text-sm h-9"
            />
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {[
              { id: "ALL", label: "All Records" },
              { id: "QUARANTINED_RED", label: "Critical" },
              { id: "CONDITIONAL_YELLOW", label: "Medium" },
              { id: "VERIFIED_GREEN", label: "Low Risk" },
              { id: "PENDING_ASSESSMENT", label: "Pending" }
            ].map(tab => (
              <Button
                key={tab.id}
                variant={statusFilter === tab.id ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setStatusFilter(tab.id)}
                className={`rounded-md text-xs px-3 h-8 ${
                  statusFilter === tab.id 
                    ? "bg-secondary text-secondary-foreground font-semibold border border-border" 
                    : "text-muted-foreground"
                }`}
              >
                {tab.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Primary Data Grid Ledger Table */}
        <Card className="rounded-md shadow-none overflow-hidden border-border">
          <Table>
            <TableHeader className="bg-muted/40 font-mono">
              <TableRow className="hover:bg-transparent border-b border-border">
                <TableHead className="py-3 pl-6">Entity</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>Control Status</TableHead>
                <TableHead>Index Score</TableHead>
                <TableHead>Internal Lead</TableHead>
                <TableHead>Last Sync</TableHead>
                <TableHead className="w-[80px] pr-6" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i} className="border-b border-border">
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j} className={`py-4 ${j === 0 ? "pl-6" : j === 6 ? "pr-6" : ""}`}>
                      <Skeleton className="h-4 w-24 rounded-md" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}

              {!loading && filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-12 text-center text-xs font-mono text-muted-foreground">
                    No records matched the filter parameters.
                  </TableCell>
                </TableRow>
              )}

              {!loading && filtered.map(v => (
                <TableRow key={v.vendor_id} className="hover:bg-muted/30 border-b border-border group transition-colors">
                  <TableCell className="py-3 pl-6 font-mono">
                    <div className="font-sans font-semibold text-foreground text-sm">{v.vendor_name}</div>
                    <div className="text-[10px] text-muted-foreground opacity-80">{v.vendor_id.slice(0, 8)}…</div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{v.vendor_type}</TableCell>
                  <TableCell>
                    {v.status && (
                      <Badge variant="outline" className={`rounded-md px-2 py-0 text-[10px] font-mono font-semibold ${STATUS_CONFIG[v.status]?.className || ""}`}>
                        {STATUS_CONFIG[v.status]?.label || v.status}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-foreground">
                        {v.current_risk_score ? Number(v.current_risk_score).toFixed(1) : "0.0"}
                      </span>
                      <ScoreTrend current={v.current_risk_score ?? "0"} previous={v.previous_risk_score ?? "0"} />
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{v.business_owner}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {new Date(v.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="py-3 pr-6 text-right">
                    <Button asChild variant="ghost" size="sm" className="h-7 text-xs px-2 text-sky-500 rounded-md opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link href={`/vendors/${v.vendor_id}`} className="flex items-center gap-1">
                        View <ChevronRight size={12} />
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  );
}