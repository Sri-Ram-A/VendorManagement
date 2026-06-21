"use client"

// # 1. Imports
import { useEffect, useMemo, useRef, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { client } from "@/lib/client"
import type { paths } from "@/types/schema"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import {
  AlertTriangle,
  Brain,
  ChevronLeft,
  ChevronsDown,
  Copy,
  Database,
  Download,
  FileText,
  Network,
  Quote,
  Scale,
  Search,
  ShieldAlert,
  Terminal,
} from "lucide-react"

// # 2. Type definitions, derived from the generated OpenAPI schema
type VendorDetail =
  paths["/api/analytics/vendors/{vendor_id}/"]["get"]["responses"]["200"]["content"]["application/json"]
type PredictResult =
  paths["/api/analytics/vendors/{vendor_id}/predict/"]["get"]["responses"]["200"]["content"]["application/json"]
type VendorDocumentItem = NonNullable<VendorDetail["documents"]>[number]

type DiscoveredAsset = {
  system_name: string
  data_sensitivity: string
}

type LogEntry = {
  id: string
  timestamp: string
  level: string
  source: string
  message: string
  textBody?: string
  jsonBody?: unknown
}

// # 3. Status metadata
// Kept identical to the registry page (same keys as Vendor.Status on the
// backend) so a vendor's stamp reads the same way everywhere in the product
const STATUS_META: Record<string, { label: string; classes: string }> = {
  PENDING: { label: "Pending", classes: "border-slate-300 bg-slate-50 text-slate-700" },
  PROCESSING: { label: "Processing", classes: "border-sky-300 bg-sky-50 text-sky-700" },
  VERIFIED: { label: "Verified", classes: "border-emerald-300 bg-emerald-50 text-emerald-700" },
  CONDITIONAL: { label: "Conditional", classes: "border-amber-300 bg-amber-50 text-amber-700" },
  QUARANTINED: { label: "Quarantined", classes: "border-rose-300 bg-rose-50 text-rose-700" },
}

// # 4. Required document metadata, mirrors the intake checklist on the
// registry page so coverage reads the same way in both places
const REQUIRED_DOCUMENTS: { code: string; label: string }[] = [
  { code: "MSA", label: "Master Services Agreement" },
  { code: "DPA", label: "Data Processing Addendum" },
  { code: "SOC2_TYPE2", label: "SOC 2 Type II Compliance Report" },
  { code: "PCI_DSS_AOC", label: "PCI-DSS Attestation of Compliance" },
]

// # 5. Extracted obligation field metadata
// Groups the freeform JSON coming back from the extraction pipeline
// (Vendor.extracted_legal_bounds) into a stable, labeled layout instead of
// dumping raw keys
type FieldType = "date" | "boolean" | "hours" | "days" | "currency" | "text" | "array"

type ObligationField = {
  key: string
  group: string
  label: string
  type: FieldType
  isWarning?: (value: unknown) => boolean
}

const OBLIGATION_GROUPS = ["Contract Timeline", "Security & Compliance", "Risk & Liability", "Data Handling"]

const OBLIGATION_FIELDS: ObligationField[] = [
  { key: "contract_start_date", group: "Contract Timeline", label: "Contract start", type: "date" },
  { key: "contract_end_date", group: "Contract Timeline", label: "Contract end", type: "date" },
  {
    key: "soc2_opinion_type",
    group: "Security & Compliance",
    label: "SOC 2 opinion",
    type: "text",
    isWarning: (v) => String(v).toLowerCase() === "qualified",
  },
  { key: "soc2_audit_period_end", group: "Security & Compliance", label: "SOC 2 audit period end", type: "date" },
  { key: "pci_dss_level", group: "Security & Compliance", label: "PCI-DSS level", type: "text" },
  { key: "pci_assessor_type", group: "Security & Compliance", label: "PCI assessor type", type: "text" },
  { key: "breach_notification_hours", group: "Risk & Liability", label: "Breach notification window", type: "hours" },
  { key: "data_return_deadline_days", group: "Risk & Liability", label: "Data return deadline", type: "days" },
  { key: "liability_cap_usd", group: "Risk & Liability", label: "Liability cap", type: "currency" },
  {
    key: "liability_uncapped_for_security_breach",
    group: "Risk & Liability",
    label: "Uncapped liability on breach",
    type: "boolean",
    isWarning: (v) => v === true || v === "true",
  },
  { key: "cert_termination_right", group: "Risk & Liability", label: "Termination right on cert lapse", type: "boolean" },
  { key: "data_categories_processed", group: "Data Handling", label: "Data categories processed", type: "array" },
]

const KNOWN_OBLIGATION_KEYS = new Set(OBLIGATION_FIELDS.map((f) => f.key))
const EXCLUDED_OBLIGATION_KEYS = new Set(["subprocessors_disclosed"])

// # 6. Section nav, drives the sticky wayfinding strip and the scrollspy
const SECTIONS = [
  { id: "overview", label: "Overview" },
  { id: "risk-signal", label: "Risk Signal" },
  { id: "obligations", label: "Obligations" },
  { id: "infrastructure", label: "Infrastructure" },
  { id: "documents", label: "Documents" },
  { id: "audit-trail", label: "Audit Trail" },
]

// # 7. Log level metadata for the audit trail viewer
const LOG_LEVEL_CLASSES: Record<string, string> = {
  ERROR: "border-rose-400/40 bg-rose-500/10 text-rose-300",
  CRITICAL: "border-rose-400/40 bg-rose-500/10 text-rose-300",
  FAIL: "border-rose-400/40 bg-rose-500/10 text-rose-300",
  WARN: "border-amber-400/40 bg-amber-500/10 text-amber-300",
  WARNING: "border-amber-400/40 bg-amber-500/10 text-amber-300",
  AI: "border-violet-400/40 bg-violet-500/10 text-violet-300",
  INFO: "border-sky-400/40 bg-sky-500/10 text-sky-300",
  SUCCESS: "border-emerald-400/40 bg-emerald-500/10 text-emerald-300",
  DEBUG: "border-slate-500/40 bg-slate-500/10 text-slate-400",
  TRACE: "border-slate-500/40 bg-slate-500/10 text-slate-400",
}

function logLevelClasses(level: string) {
  return LOG_LEVEL_CLASSES[level] ?? "border-slate-500/40 bg-slate-500/10 text-slate-400"
}

// # 8. Formatting helpers
function formatDate(value: string | null | undefined) {
  if (!value) return "—"
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
}

function formatDateTime(value: string | null | undefined) {
  if (!value) return "—"
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
}

function formatCurrency(value: unknown) {
  const num = Number(value)
  if (Number.isNaN(num)) return String(value ?? "—")
  if (num >= 1_000_000) return "$" + (num / 1_000_000).toFixed(1) + "M"
  if (num >= 1_000) return "$" + (num / 1_000).toFixed(0) + "K"
  return "$" + num.toFixed(0)
}

function formatRiskScore(value: string | undefined | null) {
  if (value === undefined || value === null || value === "") return "—"
  return Number(value).toFixed(1)
}

function humanizeKey(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatFieldValue(type: FieldType, value: unknown) {
  if (value === null || value === undefined || value === "") return "—"
  if (type === "boolean") return value === true || value === "true" ? "Yes" : "No"
  if (type === "date") return formatDate(String(value))
  if (type === "currency") return formatCurrency(value)
  if (type === "hours") return String(value) + " hrs"
  if (type === "days") return String(value) + " days"
  if (type === "array") return Array.isArray(value) ? value.join(", ") : String(value)
  return String(value)
}

// Unwraps the shapes the extraction pipeline may emit for a single field:
// a bare primitive, an array, a stringified JSON blob, or an object carrying
// { value, source_excerpt } (the provenance quote the LLM cited)
function unwrapField(raw: unknown): { value: unknown; sourceExcerpt: string | null } {
  let value = raw
  if (typeof value === "string" && (value.trim().startsWith("{") || value.trim().startsWith("["))) {
    try {
      value = JSON.parse(value)
    } catch {
      // not actually JSON, keep the raw string
    }
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const obj = value as Record<string, unknown>
    const sourceExcerpt = typeof obj.source_excerpt === "string" ? obj.source_excerpt : null
    if ("value" in obj) return { value: obj.value, sourceExcerpt }
    if ("display" in obj) return { value: obj.display, sourceExcerpt }
  }
  return { value, sourceExcerpt: null }
}

function isElevatedSensitivity(label: string) {
  const upper = (label || "").toUpperCase()
  return upper.includes("HIGH") || upper.includes("CRITICAL") || upper.includes("PCI")
}

// Splits a raw trace log into structured entries. Each entry begins with a
// "[HH:MM:SS] | LEVEL | source | message" header line; any lines that follow
// before the next header (typically a pretty-printed JSON payload from the
// LLM extraction step) are attached as that entry's body.
function parseLogEntries(raw: string): LogEntry[] {
  const headerPattern = /^\[(\d{2}:\d{2}:\d{2})\]\s*\|\s*([A-Za-z]+)\s*\|\s*([^|]+?)\s*\|\s*(.*)$/
  const lines = raw.split("\n")
  const entries: LogEntry[] = []
  let current: LogEntry | null = null
  let bodyLines: string[] = []

  function flush() {
    if (!current) return
    const bodyText = bodyLines.join("\n").trim()
    if (bodyText) {
      try {
        current.jsonBody = JSON.parse(bodyText)
      } catch {
        current.textBody = bodyText
      }
    }
    entries.push(current)
    bodyLines = []
  }

  lines.forEach((line, index) => {
    const match = headerPattern.exec(line)
    if (match) {
      flush()
      current = {
        id: String(index),
        timestamp: match[1],
        level: match[2].toUpperCase(),
        source: match[3].trim(),
        message: match[4].trim(),
      }
    } else if (current) {
      bodyLines.push(line)
    }
  })
  flush()
  return entries
}

// # 9. JSON tree renderer for log payloads, dark-terminal palette
function JsonNode({ value, depth }: { value: unknown; depth: number }) {
  if (value === null) return <span className="text-slate-500 italic">null</span>
  if (typeof value === "string") return <span className="text-emerald-300">&quot;{value}&quot;</span>
  if (typeof value === "number") return <span className="text-amber-300">{value}</span>
  if (typeof value === "boolean") return <span className="text-violet-300">{String(value)}</span>

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-slate-500">[]</span>
    return (
      <span>
        {"["}
        <div style={{ paddingLeft: 14 }}>
          {value.map((item, index) => (
            <div key={index}>
              <JsonNode value={item} depth={depth + 1} />
              {index < value.length - 1 ? "," : ""}
            </div>
          ))}
        </div>
        {"]"}
      </span>
    )
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
    if (entries.length === 0) return <span className="text-slate-500">{"{}"}</span>
    return (
      <span>
        {"{"}
        <div style={{ paddingLeft: 14 }}>
          {entries.map(([key, val], index) => (
            <div key={key}>
              <span className="text-sky-300">&quot;{key}&quot;</span>
              {": "}
              <JsonNode value={val} depth={depth + 1} />
              {index < entries.length - 1 ? "," : ""}
            </div>
          ))}
        </div>
        {"}"}
      </span>
    )
  }

  return <span>{String(value)}</span>
}

// # 10. Data hooks
function useVendorDetail(vendorId: string) {
  const [vendor, setVendor] = useState<VendorDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(
    function fetchVendor() {
      if (!vendorId) return
      let cancelled = false
        ; (async () => {
          const { data, error: err } = await client.GET("/api/analytics/vendors/{vendor_id}/", {
            params: { path: { vendor_id: vendorId } },
          })
          if (cancelled) return
          if (err || !data) {
            setError("Vendor compliance record not resolved.")
          } else {
            setVendor(data)
          }
          setLoading(false)
        })()
      return function cleanup() {
        cancelled = true
      }
    },
    [vendorId]
  )

  return { vendor, loading, error }
}

function usePrediction(vendorId: string) {
  const [prediction, setPrediction] = useState<PredictResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(
    function fetchPrediction() {
      if (!vendorId) return
      let cancelled = false
        ; (async () => {
          const { data } = await client.GET("/api/analytics/vendors/{vendor_id}/predict/", {
            params: { path: { vendor_id: vendorId } },
          })
          if (!cancelled && data) setPrediction(data)
          if (!cancelled) setLoading(false)
        })()
      return function cleanup() {
        cancelled = true
      }
    },
    [vendorId]
  )

  return { prediction, loading }
}

function useScrollSpy(ids: string[]) {
  const [activeId, setActiveId] = useState(ids[0])
  const idsKey = ids.join(",")

  useEffect(
    function observeSections() {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) setActiveId(entry.target.id)
          })
        },
        { rootMargin: "-20% 0px -70% 0px", threshold: 0 }
      )
      ids.forEach((id) => {
        const el = document.getElementById(id)
        if (el) observer.observe(el)
      })
      return function cleanup() {
        observer.disconnect()
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    [idsKey]
  )

  return activeId
}

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" })
}

// # 11. Page component
export default function VendorDetailPage() {
  const params = useParams()
  const vendorId = String(params?.vendor_id ?? "")
  const { vendor, loading, error } = useVendorDetail(vendorId)
  const { prediction, loading: predLoading } = usePrediction(vendorId)
  const activeSection = useScrollSpy(SECTIONS.map((s) => s.id))

  // # 11.1 Audit trail viewer state
  const [logContent, setLogContent] = useState<string | null>(null)
  const [fetchingLog, setFetchingLog] = useState(false)
  const [logError, setLogError] = useState<string | null>(null)
  const [isLogOpen, setIsLogOpen] = useState(false)
  const [logSearch, setLogSearch] = useState("")
  const [excludedLevels, setExcludedLevels] = useState<Set<string>>(new Set())
  const [expandedJsonIds, setExpandedJsonIds] = useState<Set<string>>(new Set())
  const logScrollRef = useRef<HTMLDivElement>(null)

  // # 11.2 Obligation evidence toggle state
  const [openExcerptKeys, setOpenExcerptKeys] = useState<Set<string>>(new Set())

  // # 11.3 Derived vendor data
  const legalBounds = (vendor?.extracted_legal_bounds as Record<string, unknown>) ?? {}
  const dataCategories = (vendor?.declared_data_categories as string[]) ?? []
  const declaredSystems = vendor?.declared_systems_accessed
    ? String(vendor.declared_systems_accessed)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
    : []
  const discoveredInfrastructure = (vendor?.discovered_infrastructure as DiscoveredAsset[]) ?? []
  const subprocessors = (legalBounds["subprocessors_disclosed"] as string[]) ?? []
  const documents: VendorDocumentItem[] = vendor?.documents ?? []

  const riskDelta =
    vendor && vendor.current_risk_score !== undefined && vendor.previous_risk_score !== undefined
      ? Number(vendor.current_risk_score) - Number(vendor.previous_risk_score)
      : null

  const documentsByType = new Map<string, VendorDocumentItem>()
  documents.forEach((doc) => {
    if (!documentsByType.has(doc.document_type)) documentsByType.set(doc.document_type, doc)
  })
  const missingDocumentCount = REQUIRED_DOCUMENTS.filter((req) => !documentsByType.has(req.code)).length

  const declaredSystemNames = new Set(declaredSystems.map((s) => s.toLowerCase()))
  const infrastructureWithDrift = discoveredInfrastructure.map((asset) => ({
    ...asset,
    isUndeclared: !declaredSystemNames.has((asset.system_name || "").toLowerCase()),
  }))
  const undeclaredCount = infrastructureWithDrift.filter((a) => a.isUndeclared).length

  const otherObligationKeys = Object.keys(legalBounds).filter(
    (key) => !KNOWN_OBLIGATION_KEYS.has(key) && !EXCLUDED_OBLIGATION_KEYS.has(key)
  )

  // # 11.4 Audit trail derived data
  const logEntries = useMemo(() => (logContent ? parseLogEntries(logContent) : []), [logContent])
  const presentLevels = useMemo(() => Array.from(new Set(logEntries.map((e) => e.level))), [logEntries])
  const filteredLogEntries = useMemo(() => {
    const term = logSearch.trim().toLowerCase()
    return logEntries.filter((entry) => {
      if (excludedLevels.has(entry.level)) return false
      if (!term) return true
      const haystack = (
        entry.message +
        " " +
        entry.source +
        " " +
        (entry.textBody ?? "") +
        " " +
        JSON.stringify(entry.jsonBody ?? "")
      ).toLowerCase()
      return haystack.includes(term)
    })
  }, [logEntries, logSearch, excludedLevels])
  const errorCount = logEntries.filter((e) => e.level === "ERROR" || e.level === "CRITICAL").length
  const warnCount = logEntries.filter((e) => e.level === "WARN" || e.level === "WARNING").length

  // # 11.5 Handlers
  function toggleLevel(level: string) {
    setExcludedLevels((previous) => {
      const next = new Set(previous)
      if (next.has(level)) next.delete(level)
      else next.add(level)
      return next
    })
  }

  function toggleExcerpt(key: string) {
    setOpenExcerptKeys((previous) => {
      const next = new Set(previous)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  function toggleJson(id: string) {
    setExpandedJsonIds((previous) => {
      const next = new Set(previous)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function openLogViewer(url: string) {
    setIsLogOpen(true)
    setFetchingLog(true)
    setLogError(null)
    setLogSearch("")
    setExcludedLevels(new Set())
    try {
      const response = await fetch(url)
      if (!response.ok) throw new Error("Could not read pipeline artifact logs.")
      const text = await response.text()
      setLogContent(text)
    } catch (err) {
      setLogError(err instanceof Error ? err.message : "Failed to stream audit file.")
    } finally {
      setFetchingLog(false)
    }
  }

  async function copyLog() {
    if (!logContent) return
    await navigator.clipboard.writeText(logContent)
  }

  function downloadLog() {
    if (!logContent || !vendor?.execution_trace_log) return
    const blob = new Blob([logContent], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = vendor.execution_trace_log.split("/").pop() || "execution_trace.log"
    anchor.click()
    URL.revokeObjectURL(url)
  }

  function jumpToLatest() {
    const el = logScrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }

  // # 11.6 Error state
  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="max-w-sm rounded-sm border border-rose-300 bg-rose-50 px-6 py-8 text-center">
          <AlertTriangle className="mx-auto h-5 w-5 text-rose-600" />
          <p className="mt-3 text-sm text-rose-700">{error}</p>
          <Link href="/" className="mt-4 inline-block text-xs font-medium text-rose-700 underline underline-offset-2">
            Return to the registry
          </Link>
        </div>
      </div>
    )
  }

  const statusMeta = vendor ? STATUS_META[vendor.status] ?? STATUS_META.PENDING : null

  // # 11.7 Render
  return (
    <div className="min-h-screen bg-background max-w-7xl mx-auto text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/"
              aria-label="Back to the registry"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <ChevronLeft className="h-4 w-4" />
            </Link>
            <div className="min-w-0">
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Inspection Ledger
              </p>
              {loading ? (
                <Skeleton className="mt-1 h-5 w-48 rounded-sm" />
              ) : (
                <div className="flex items-baseline gap-2">
                  <h1 className="truncate text-lg font-semibold tracking-tight">{vendor?.vendor_name}</h1>
                  <span className="shrink-0 text-xs text-muted-foreground">{vendor?.vendor_type}</span>
                </div>
              )}
            </div>
          </div>
          {statusMeta && (
            <span
              className={
                "shrink-0 -rotate-3 rounded-sm border px-3 py-1 font-mono text-[11px] font-bold uppercase tracking-widest " +
                statusMeta.classes
              }
            >
              {statusMeta.label}
            </span>
          )}
        </div>

        {/* Section wayfinding strip, doubles as a scrollspy */}
        <nav aria-label="Vendor record sections" className="border-t border-border">
          <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-6 py-2">
            {SECTIONS.map((section) => (
              <button
                key={section.id}
                type="button"
                onClick={function onSelect() {
                  scrollToSection(section.id)
                }}
                className={
                  "shrink-0 rounded-sm border px-3 py-1.5 font-mono text-[11px] uppercase tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                  (activeSection === section.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-transparent text-muted-foreground hover:bg-muted")
                }
              >
                {section.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl space-y-12 px-6 py-8">
        {/* Overview */}
        <section id="overview" style={{ scrollMarginTop: "112px" }} className="space-y-4">
          <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">Overview</p>

          {loading ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded-sm" />
              ))}
            </div>
          ) : (
            vendor && (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
                <div className="rounded-sm border border-border bg-card px-4 py-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Risk score</p>
                  <div className="mt-1 flex items-baseline gap-1.5 font-mono text-xl">
                    {formatRiskScore(vendor.current_risk_score)}
                    {riskDelta !== null && riskDelta !== 0 && (
                      <span className={"text-xs " + (riskDelta > 0 ? "text-rose-600" : "text-emerald-600")}>
                        {riskDelta > 0 ? "▲" : "▼"} {Math.abs(riskDelta).toFixed(1)}
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    prev {formatRiskScore(vendor.previous_risk_score)}
                  </p>
                </div>

                <div className="rounded-sm border border-border bg-card px-4 py-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Annual spend</p>
                  <p className="mt-1 font-mono text-xl">
                    {vendor.annual_spend ? formatCurrency(vendor.annual_spend) : "—"}
                  </p>
                </div>

                <div className="rounded-sm border border-border bg-card px-4 py-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Business owner</p>
                  <p className="mt-1 truncate text-base font-medium">{vendor.business_owner}</p>
                </div>

                <button
                  type="button"
                  onClick={function goToDocuments() {
                    scrollToSection("documents")
                  }}
                  className="rounded-sm border border-border bg-card px-4 py-3 text-left transition-colors hover:border-foreground/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Document coverage</p>
                  <p className={"mt-1 font-mono text-xl " + (missingDocumentCount > 0 ? "text-amber-600" : "")}>
                    {REQUIRED_DOCUMENTS.length - missingDocumentCount} / {REQUIRED_DOCUMENTS.length}
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {missingDocumentCount > 0 ? missingDocumentCount + " required missing" : "All required on file"}
                  </p>
                </button>

                <div className="rounded-sm border border-border bg-card px-4 py-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Filed</p>
                  <p className="mt-1 font-mono text-sm">{formatDate(vendor.created_at)}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">synced {formatDateTime(vendor.updated_at)}</p>
                </div>
              </div>
            )
          )}

          <div className="rounded-sm border border-border bg-card p-4">
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">AI narrative summary</p>
            {loading ? (
              <div className="mt-2 space-y-2">
                <Skeleton className="h-4 w-full rounded-sm" />
                <Skeleton className="h-4 w-[85%] rounded-sm" />
              </div>
            ) : (
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {typeof vendor?.risk_narrative_summary === "string" && vendor.risk_narrative_summary
                  ? vendor.risk_narrative_summary
                  : "No risk narrative generated yet. Document extraction must complete before pipeline processing begins."}
              </p>
            )}
          </div>
        </section>

        {/* Risk Signal */}
        <section id="risk-signal" style={{ scrollMarginTop: "112px" }} className="space-y-3">
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-muted-foreground" />
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              ML Inference Telemetry
            </p>
          </div>

          <div className="rounded-sm border border-border bg-card p-4">
            {predLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-5 w-1/3 rounded-sm" />
                <Skeleton className="h-16 w-full rounded-sm" />
              </div>
            ) : prediction && Object.keys(prediction).length > 0 ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span
                    className={
                      "inline-flex items-center gap-1.5 rounded-sm border px-2.5 py-1 font-mono text-[11px] font-semibold uppercase tracking-wide " +
                      (prediction.is_anomaly
                        ? "border-rose-300 bg-rose-50 text-rose-700"
                        : "border-emerald-300 bg-emerald-50 text-emerald-700")
                    }
                  >
                    {prediction.is_anomaly ? <AlertTriangle className="h-3 w-3" /> : null}
                    {prediction.is_anomaly ? "Anomalous signature" : "Nominal compliance"}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Confidence <span className="font-mono font-semibold text-foreground">{String(prediction.confidence ?? "—")}</span>
                  </span>
                </div>

                {prediction.all_probs && (
                  <div className="space-y-2.5 border-t border-border pt-3">
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                      Classification probability density
                    </p>
                    {Object.entries(prediction.all_probs as Record<string, number>)
                      .sort(([, a], [, b]) => b - a)
                      .map(([cls, prob]) => (
                        <div key={cls} className="space-y-1">
                          <div className="flex justify-between font-mono text-xs">
                            <span className="capitalize text-muted-foreground">{cls.replace(/_/g, " ")}</span>
                            <span className="font-semibold">{(prob * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 overflow-hidden rounded-sm bg-muted">
                            <div className="h-full bg-foreground" style={{ width: prob * 100 + "%" }} />
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Inference logs not generated for target pipeline.</p>
            )}
          </div>
        </section>

        {/* Obligations */}
        <section id="obligations" style={{ scrollMarginTop: "112px" }} className="space-y-3">
          <div className="flex items-center gap-2">
            <Scale className="h-4 w-4 text-muted-foreground" />
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Extracted Contract Obligations
            </p>
          </div>

          {loading ? (
            <Skeleton className="h-48 w-full rounded-sm" />
          ) : Object.keys(legalBounds).length === 0 ? (
            <div className="rounded-sm border border-dashed border-border px-6 py-10 text-center">
              <p className="text-sm text-muted-foreground">
                No active obligations parsed. Upload corporate records to invoke pipeline parsing analysis.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
              {OBLIGATION_GROUPS.map((group) => {
                const fields = OBLIGATION_FIELDS.filter((f) => f.group === group)
                const visibleFields = fields.filter((f) => legalBounds[f.key] !== undefined)
                if (visibleFields.length === 0) return null
                return (
                  <div key={group} className="rounded-sm border border-border bg-card p-4">
                    <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">{group}</p>
                    <dl className="mt-3 space-y-3">
                      {visibleFields.map((field) => {
                        const { value, sourceExcerpt } = unwrapField(legalBounds[field.key])
                        const isWarning = field.isWarning ? field.isWarning(value) : false
                        const excerptKey = field.key
                        return (
                          <div key={field.key} className="border-b border-border pb-2 last:border-b-0 last:pb-0">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                                  {field.label}
                                </dt>
                                <dd
                                  className={
                                    "mt-0.5 font-mono text-sm font-semibold " +
                                    (isWarning ? "text-rose-600" : "text-foreground")
                                  }
                                >
                                  {formatFieldValue(field.type, value)}
                                </dd>
                              </div>
                              {sourceExcerpt && (
                                <button
                                  type="button"
                                  onClick={function onToggleExcerpt() {
                                    toggleExcerpt(excerptKey)
                                  }}
                                  title="View source excerpt"
                                  className="mt-0.5 shrink-0 rounded-sm p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                                >
                                  <Quote className="h-3.5 w-3.5" />
                                </button>
                              )}
                            </div>
                            {sourceExcerpt && openExcerptKeys.has(excerptKey) && (
                              <blockquote className="mt-2 rounded-sm border border-border bg-muted/40 px-3 py-2 text-xs italic leading-relaxed text-muted-foreground">
                                &ldquo;{sourceExcerpt}&rdquo;
                              </blockquote>
                            )}
                          </div>
                        )
                      })}
                    </dl>
                  </div>
                )
              })}

              {otherObligationKeys.length > 0 && (
                <div className="rounded-sm border border-dashed border-border p-4 lg:col-span-2">
                  <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                    Other extracted fields
                  </p>
                  <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {otherObligationKeys.map((key) => {
                      const { value } = unwrapField(legalBounds[key])
                      const display = Array.isArray(value) ? value.join(", ") : String(value ?? "—")
                      return (
                        <div key={key}>
                          <dt className="text-[11px] uppercase tracking-wide text-muted-foreground">
                            {humanizeKey(key)}
                          </dt>
                          <dd className="mt-0.5 font-mono text-sm">{display}</dd>
                        </div>
                      )
                    })}
                  </dl>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Infrastructure */}
        <section id="infrastructure" style={{ scrollMarginTop: "112px" }} className="space-y-3">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-muted-foreground" />
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Data & Infrastructure Boundaries
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div className="rounded-sm border border-border bg-card p-4">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Asset classes exchanged</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {dataCategories.length ? (
                  dataCategories.map((cat) => (
                    <span
                      key={cat}
                      className={
                        "rounded-sm border px-2 py-0.5 font-mono text-[11px] " +
                        (["PCI_CARDHOLDER_DATA", "CREDENTIALS_AUTH"].includes(cat)
                          ? "border-rose-300 bg-rose-50 text-rose-700"
                          : "border-border bg-muted text-muted-foreground")
                      }
                    >
                      {cat}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">No cataloged operational categories.</p>
                )}
              </div>

              <p className="mt-4 text-[11px] uppercase tracking-wide text-muted-foreground">
                Downstream subprocessors
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {subprocessors.length ? (
                  subprocessors.map((sp) => (
                    <span
                      key={sp}
                      className="rounded-sm border border-border bg-muted px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                    >
                      {sp}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">No nested third parties disclosed in contract terms.</p>
                )}
              </div>
            </div>

            <div className="rounded-sm border border-border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                  Declared vs. discovered systems
                </p>
                {undeclaredCount > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-sm border border-amber-300 bg-amber-50 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase text-amber-700">
                    <ShieldAlert className="h-3 w-3" />
                    {undeclaredCount} undeclared
                  </span>
                )}
              </div>

              <p className="mt-1 text-[11px] text-muted-foreground">
                Systems the business owner declared at intake vs. systems the automated scan actually found touching
                this vendor.
              </p>

              <div className="mt-3 space-y-1.5">
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Declared at intake</p>
                <div className="flex flex-wrap gap-1.5">
                  {declaredSystems.length ? (
                    declaredSystems.map((s) => (
                      <span
                        key={s}
                        className="rounded-sm border border-border bg-muted px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                      >
                        {s}
                      </span>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">No systems declared.</p>
                  )}
                </div>
              </div>

              <div className="mt-3 space-y-1.5 border-t border-border pt-3">
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Discovered by automated scan</p>
                {infrastructureWithDrift.length ? (
                  <ul className="space-y-1">
                    {infrastructureWithDrift.map((asset, index) => (
                      <li
                        key={asset.system_name + index}
                        className={
                          "flex items-center justify-between gap-2 rounded-sm border px-2.5 py-1.5 " +
                          (asset.isUndeclared ? "border-amber-300 bg-amber-50" : "border-border bg-background")
                        }
                      >
                        <span className="font-mono text-xs">{asset.system_name}</span>
                        <div className="flex items-center gap-1.5">
                          {asset.isUndeclared && (
                            <span className="font-mono text-[10px] font-semibold uppercase text-amber-700">
                              Undeclared
                            </span>
                          )}
                          <span
                            className={
                              "rounded-sm border px-1.5 py-0.5 font-mono text-[10px] " +
                              (isElevatedSensitivity(asset.data_sensitivity)
                                ? "border-rose-300 bg-rose-50 text-rose-700"
                                : "border-border bg-muted text-muted-foreground")
                            }
                          >
                            {asset.data_sensitivity}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-muted-foreground">No infrastructure discovered for this vendor yet.</p>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Documents */}
        <section id="documents" style={{ scrollMarginTop: "112px" }} className="space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Secured Document Vault
            </p>
          </div>

          <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
            {REQUIRED_DOCUMENTS.map((req) => {
              const matched = documentsByType.get(req.code)
              return (
                <div key={req.code} className="flex items-center gap-2 rounded-sm border border-border px-3 py-2">
                  <span className={"h-1.5 w-1.5 shrink-0 rounded-full " + (matched ? "bg-emerald-600" : "bg-muted-foreground/40")} />
                  <div className="min-w-0">
                    <p className="truncate text-xs">{req.label}</p>
                    <p className="text-[10px] text-muted-foreground">{matched ? "Attached" : "Missing"}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="overflow-hidden rounded-sm border border-border">
            {loading ? (
              <div className="p-4">
                <Skeleton className="h-16 w-full rounded-sm" />
              </div>
            ) : documents.length > 0 ? (
              <Table>
                <TableHeader className="bg-muted/40">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="pl-4 font-mono text-[11px] uppercase tracking-wide">Document</TableHead>
                    <TableHead className="font-mono text-[11px] uppercase tracking-wide">Type</TableHead>
                    <TableHead className="font-mono text-[11px] uppercase tracking-wide">Validity</TableHead>
                    <TableHead className="font-mono text-[11px] uppercase tracking-wide">Pipeline</TableHead>
                    <TableHead className="font-mono text-[11px] uppercase tracking-wide">Issued</TableHead>
                    <TableHead className="font-mono text-[11px] uppercase tracking-wide">Expires</TableHead>
                    <TableHead className="pr-4 text-right font-mono text-[11px] uppercase tracking-wide">
                      Uploaded
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="font-mono text-xs">
                  {documents.map((doc) => (
                    <TableRow key={doc.document_id} className="border-b last:border-0">
                      <TableCell className="pl-4 py-3">
                        <div className="flex items-center gap-2">
                          <FileText className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                          <span className="truncate">{doc.document_reference || doc.document_id}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-sans">{doc.document_type}</TableCell>
                      <TableCell>
                        <span
                          className={
                            "rounded-sm border px-1.5 py-0.5 font-sans text-[10px] " +
                            (doc.is_expired
                              ? "border-rose-300 bg-rose-50 text-rose-700"
                              : "border-emerald-300 bg-emerald-50 text-emerald-700")
                          }
                        >
                          {doc.is_expired ? "Expired" : "Active"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={
                            "text-[11px] font-bold " +
                            (doc.extraction_status === "SUCCESS"
                              ? "text-emerald-600"
                              : doc.extraction_status === "FAILED"
                                ? "text-rose-600"
                                : "text-sky-600")
                          }
                        >
                          ● {doc.extraction_status}
                        </span>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{formatDate(doc.issued_date)}</TableCell>
                      <TableCell className="text-muted-foreground">{formatDate(doc.expiry_date)}</TableCell>
                      <TableCell className="pr-4 text-right text-muted-foreground">
                        {formatDate(doc.uploaded_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <p className="p-6 text-center text-xs text-muted-foreground">
                No documents mapped onto this vendor record yet.
              </p>
            )}
          </div>
        </section>

        {/* Audit Trail */}
        {vendor?.execution_trace_log && (
          <section id="audit-trail" style={{ scrollMarginTop: "112px" }} className="space-y-3">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-muted-foreground" />
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Pipeline Audit Trail
              </p>
            </div>
            <div className="flex items-center justify-between rounded-sm border border-border bg-muted/30 px-4 py-3">
              <p className="truncate font-mono text-xs text-muted-foreground">
                {vendor.execution_trace_log.split("/").pop()}
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 shrink-0 rounded-sm font-mono text-xs"
                onClick={function onInspect() {
                  openLogViewer(vendor.execution_trace_log as string)
                }}
              >
                Inspect system logs
              </Button>
            </div>
          </section>
        )}
      </main>

      {/* Audit trail viewer */}
      <Dialog open={isLogOpen} onOpenChange={setIsLogOpen}>
        <DialogContent
          className="flex h-[92vh] w-full max-w-[96vw] flex-col gap-0 rounded-md border p-0 font-mono shadow-2xl transition-colors duration-200
          /* Light Mode: Classic Linux / macOS Terminal */
          bg-[#F5F5F5] text-[#24292E] border-slate-300
          /* Dark Mode: VS Code / Monokai IDE Terminal */
          dark:bg-[#1E1E1E] dark:text-[#D4D4D4] dark:border-[#2D2D2D] 
          sm:max-w-[96vw]"
        >
          {/* Terminal Header Bar */}
          <DialogHeader
            className="shrink-0 flex flex-row items-center justify-between border-b px-5 py-3 
            bg-[#E8E8E8] border-slate-300
            dark:bg-[#252526] dark:border-[#2D2D2D]"
          >
            {/* Fake Window OS Actions (Red, Yellow, Green Window Dots) */}
            <div className="flex items-center gap-1.5 shrink-0 select-none">
              <span className="w-3 h-3 rounded-full bg-[#FF5F56] border border-[#E0443E]" />
              <span className="w-3 h-3 rounded-full bg-[#FFBD2E] border border-[#DEA123]" />
              <span className="w-3 h-3 rounded-full bg-[#27C93F] border border-[#1AAB29]" />

              {/* Split Title Tag */}
              <DialogTitle className="ml-3 flex items-center gap-2 text-xs font-bold font-mono tracking-tight text-slate-700 dark:text-slate-300">
                <Terminal className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
                <span>{vendor?.execution_trace_log?.split("/").pop() || "execution_trace.log"}</span>
              </DialogTitle>
            </div>

            <DialogDescription className="hidden md:inline font-mono text-[11px] text-slate-500 dark:text-slate-400">
              bash ~ pipeline_audit_stream.sh
            </DialogDescription>
          </DialogHeader>

          {/* Action Controls & Input Terminal Strip */}
          {!fetchingLog && !logError && logContent !== null && (
            <div
              className="flex shrink-0 flex-wrap items-center gap-3 border-b px-5 py-2.5 text-xs
              bg-[#EDF2F7] border-slate-300
              dark:bg-[#1C1C1C] dark:border-[#2D2D2D]"
            >
              {/* Terminal Command Style Prompt Input */}
              <div className="relative flex-1 min-w-55">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-emerald-600 dark:text-emerald-400 font-bold select-none text-[11px]">
                  $
                </span>
                <input
                  type="text"
                  value={logSearch}
                  onChange={(e) => setLogSearch(e.target.value)}
                  placeholder="grep log entries..."
                  className="w-full rounded-md border py-1 pl-6 pr-2 font-mono text-xs transition-all focus-visible:outline-none focus-visible:ring-1
                  bg-white text-slate-900 border-slate-300 placeholder:text-slate-400 focus-visible:ring-slate-400
                  dark:bg-[#2D2D2D] dark:text-slate-100 dark:border-zinc-700 dark:placeholder:text-zinc-500 dark:focus-visible:ring-sky-500"
                />
              </div>

              {/* Level Toggle Badges */}
              <div className="flex flex-wrap items-center gap-1">
                {presentLevels.map((level) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => toggleLevel(level)}
                    className={`rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide font-semibold transition-all ${logLevelClasses(level)} ${excludedLevels.has(level) ? "opacity-25 grayscale line-through" : "opacity-100"
                      }`}
                  >
                    {level}
                  </button>
                ))}
              </div>

              {/* Action Bar Dropdowns */}
              <div className="flex items-center gap-1">
                {[
                  { icon: <ChevronsDown className="h-3.5 w-3.5" />, action: jumpToLatest, label: "Jump to latest logs" },
                  { icon: <Copy className="h-3.5 w-3.5" />, action: copyLog, label: "Copy dump" },
                  { icon: <Download className="h-3.5 w-3.5" />, action: downloadLog, label: "Download file" }
                ].map((btn, i) => (
                  <Button
                    key={i}
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={btn.action}
                    title={btn.label}
                    className="h-7 w-8 p-0 rounded-md shadow-none transition-colors
                    border-slate-300 bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900
                    dark:border-zinc-700 dark:bg-[#2D2D2D] dark:text-zinc-300 dark:hover:bg-[#3C3C3C] dark:hover:text-white"
                  >
                    {btn.icon}
                  </Button>
                ))}
              </div>

              {/* Metadata Count Tracker */}
              <p className="ml-auto font-mono text-[11px] text-slate-500 dark:text-zinc-400 select-none">
                {filteredLogEntries.length}/{logEntries.length} entries
                {errorCount > 0 && <span className="text-rose-600 dark:text-rose-400 font-bold"> · {errorCount} errors</span>}
                {warnCount > 0 && <span className="text-amber-600 dark:text-amber-400 font-bold"> · {warnCount} warnings</span>}
              </p>
            </div>
          )}

          {/* Log Stream Output Stream Console Screen */}
          <div
            ref={logScrollRef}
            className="min-h-0 flex-1 overflow-y-auto px-4 py-3 selection:bg-sky-500/30
            bg-white
            dark:bg-[#181818]"
          >
            {fetchingLog && (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-xs text-slate-400 dark:text-zinc-500">
                <Database className="h-4 w-4 animate-pulse text-sky-500" />
                <span>Streaming remote log data bytes...</span>
              </div>
            )}

            {logError && (
              <div className="flex h-full items-center justify-center text-xs font-bold text-rose-600 dark:text-rose-400">
                [SYSTEM FAULT]: {logError}
              </div>
            )}

            {!fetchingLog && !logError && logContent !== null && (
              <div className="space-y-1">
                {filteredLogEntries.length === 0 ? (
                  <p className="px-2 py-8 text-center text-xs italic text-slate-400 dark:text-zinc-600">
                    No entries match the current grep execution parameters.
                  </p>
                ) : (
                  filteredLogEntries.map((entry) => (
                    <div key={entry.id} className="rounded-md px-2 py-0.5 transition-colors hover:bg-slate-100 dark:hover:bg-white/[0.02]">
                      <div className="flex flex-wrap items-baseline gap-x-2.5 font-mono text-[11px] leading-relaxed">
                        {/* Timestamp */}
                        <span className="text-slate-400 dark:text-zinc-500 select-none">
                          {entry.timestamp}
                        </span>

                        {/* Log Level */}
                        <span className={`rounded-md border px-1.5 py-0.5 text-[9px] font-bold tracking-wide select-none ${logLevelClasses(entry.level)}`}>
                          {entry.level}
                        </span>

                        {/* Code Execution Origin Context */}
                        <span className="text-indigo-600 dark:text-sky-400 opacity-80">
                          [{entry.source}]
                        </span>

                        {/* Text Message */}
                        <span className="text-slate-800 dark:text-zinc-200 break-all">
                          {entry.message}
                        </span>
                      </div>

                      {/* Nested Stack Traces Text Blocks */}
                      {entry.textBody && (
                        <pre className="mt-1.5 whitespace-pre-wrap break-words rounded-md border px-3 py-2 text-[11px] transition-colors
                        border-slate-200 bg-slate-50 text-slate-700
                        dark:border-zinc-800 dark:bg-[#252526] dark:text-zinc-400">
                          {entry.textBody}
                        </pre>
                      )}

                      {/* Integrated JSON Object Node Tree */}
                      {entry.jsonBody !== undefined && (
                        <div className="mt-1.5 rounded-md border px-3 py-1.5
                        border-slate-200 bg-slate-50
                        dark:border-zinc-800 dark:bg-[#252526]">
                          <button
                            type="button"
                            onClick={() => toggleJson(entry.id)}
                            className="text-[11px] font-semibold text-sky-600 hover:underline dark:text-sky-400 flex items-center gap-1"
                          >
                            {expandedJsonIds.has(entry.id) ? "[-] Minimize" : "[+] Inspect"} payload object
                          </button>
                          {expandedJsonIds.has(entry.id) && (
                            <div className="mt-2 overflow-x-auto border-t pt-1.5 border-slate-200 dark:border-zinc-700 text-[11px] leading-relaxed">
                              <JsonNode value={entry.jsonBody} depth={0} />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}