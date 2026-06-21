"use client"

// # 1. Imports
import { useEffect, useRef, useState } from "react"
import type { ChangeEvent, DragEvent, FormEvent, KeyboardEvent } from "react"
import { useRouter } from "next/navigation"
import {
  Building2,
  ChevronRight,
  FileText,
  LayoutGrid,
  List,
  Loader2,
  MoreVertical,
  Plus,
  TrendingDown,
  TrendingUp,
  Upload,
  X,
} from "lucide-react"
import { client } from "@/lib/client"
import type { components } from "@/types/schema"
import { ThemeToggle } from "@/components/theme-toggle";

// # 2. Type definitions
type VendorListItem = components["schemas"]["VendorList"]
type VendorStatus = components["schemas"]["StatusEnum"]
type DataCategory = components["schemas"]["DeclaredDataCategoriesEnum"]
type ViewMode = "grid" | "row"
type StatusFilter = VendorStatus | "ALL"

// # 3. Status metadata
// Drives both the filter strip and the stamp shown on every vendor record
const STATUS_SEQUENCE: VendorStatus[] = [
  "PENDING",
  "PROCESSING",
  "VERIFIED",
  "CONDITIONAL",
  "QUARANTINED",
]

const STATUS_META: Record<VendorStatus, { label: string; description: string; classes: string }> = {
  PENDING: {
    label: "Pending",
    description: "Pending Assessment",
    classes: "border-slate-300 bg-slate-50 text-slate-700",
  },
  PROCESSING: {
    label: "Processing",
    description: "Processing Ingestion Pipeline",
    classes: "border-sky-300 bg-sky-50 text-sky-700",
  },
  VERIFIED: {
    label: "Verified",
    description: "Verified Low Risk",
    classes: "border-emerald-300 bg-emerald-50 text-emerald-700",
  },
  CONDITIONAL: {
    label: "Conditional",
    description: "Conditional Medium Risk",
    classes: "border-amber-300 bg-amber-50 text-amber-700",
  },
  QUARANTINED: {
    label: "Quarantined",
    description: "Critical High Risk, Action Required",
    classes: "border-rose-300 bg-rose-50 text-rose-700",
  },
}

// # 4. Declared data category metadata
// Mirrors Vendor.DataCategory choices on the backend, used to populate the add menu
const DATA_CATEGORY_SEQUENCE: DataCategory[] = [
  "PCI_CARDHOLDER_DATA",
  "CUSTOMER_PII",
  "CREDENTIALS_AUTH",
  "FINANCIAL_RECORDS",
  "PUBLIC_MARKETING",
]

const DATA_CATEGORY_META: Record<DataCategory, string> = {
  PCI_CARDHOLDER_DATA: "Credit Card Details / PAN / CVV",
  CUSTOMER_PII: "Personally Identifiable Info (Names, Addresses)",
  CREDENTIALS_AUTH: "Authentication Hashes / API Tokens",
  FINANCIAL_RECORDS: "Corporate Accounting / Trade Ledger Data",
  PUBLIC_MARKETING: "Publicly Available Marketing Assets",
}

// # 5. Document requirement metadata
// File names are matched against these keywords to auto sort uploads, mirroring the
// ingestion serializer help text on the backend
type DocumentRequirement = {
  code: string
  label: string
  description: string
  keywords: string[]
  keywordHint: string
}

const DOCUMENT_REQUIREMENTS: DocumentRequirement[] = [
  {
    code: "MSA",
    label: "Master Services Agreement",
    description: "The core commercial contract governing the relationship with this vendor.",
    keywords: ["MSA"],
    keywordHint: "File name must contain MSA",
  },
  {
    code: "DPA",
    label: "Data Processing Addendum",
    description: "Sets out how the vendor is permitted to handle and protect shared data.",
    keywords: ["DPA"],
    keywordHint: "File name must contain DPA",
  },
  {
    code: "SOC2_TYPE2",
    label: "SOC 2 Type II Compliance Report",
    description: "Independent audit evidence covering the vendor's controls over time.",
    keywords: ["SOC"],
    keywordHint: "File name must contain SOC",
  },
  {
    code: "PCI_DSS_AOC",
    label: "PCI-DSS Attestation of Compliance",
    description: "Confirms the vendor meets card processing security standards.",
    keywords: ["PCI", "AOC"],
    keywordHint: "File name must contain PCI or AOC",
  },
]

// # 6. Helper functions
function detectDocumentType(fileName: string) {
  const upperName = fileName.toUpperCase()
  for (const requirement of DOCUMENT_REQUIREMENTS) {
    for (const keyword of requirement.keywords) {
      if (upperName.includes(keyword)) {
        return requirement.code
      }
    }
  }
  return null
}

function formatDate(isoString: string) {
  const parsed = new Date(isoString)
  return parsed.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

function formatRiskScore(score: string | undefined) {
  if (score === undefined || score === null || score === "") {
    return "—"
  }
  return Number(score).toFixed(1)
}

function getRiskDelta(current: string | undefined, previous: string | undefined) {
  if (current === undefined || previous === undefined || current === "" || previous === "") {
    return null
  }
  return Number(current) - Number(previous)
}

function pluralize(count: number, noun: string) {
  return count === 1 ? noun : noun + "s"
}

// # 7. Page component
export default function HomePage() {
  const router = useRouter()

  // # 7.1 UseStates configuration, vendor registry
  const [vendors, setVendors] = useState<VendorListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>("grid")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL")

  // # 7.2 UseStates configuration, intake drawer
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [vendorName, setVendorName] = useState("")
  const [vendorType, setVendorType] = useState("")
  const [businessOwner, setBusinessOwner] = useState("")
  const [annualSpend, setAnnualSpend] = useState("")
  const [selectedCategories, setSelectedCategories] = useState<DataCategory[]>([])
  const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false)
  const [systemInput, setSystemInput] = useState("")
  const [systems, setSystems] = useState<string[]>([])
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [openInfoCode, setOpenInfoCode] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // # 7.3 Effects
  useEffect(function loadOnMount() {
    loadVendors()
  }, [])

  useEffect(function bindEscapeKey() {
    function handleKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") {
        closeDrawer()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return function cleanup() {
      window.removeEventListener("keydown", handleKeyDown)
    }
  }, [])

  // # 7.4 Registry data handlers
  async function loadVendors() {
    setIsLoading(true)
    setLoadError(null)
    const result = await client.GET("/api/analytics/vendors/")
    if (result.error) {
      setLoadError("The registry could not be reached. Try refreshing the page.")
      setIsLoading(false)
      return
    }
    setVendors(result.data ?? [])
    setIsLoading(false)
  }

  function setGridView() {
    setViewMode("grid")
  }

  function setRowView() {
    setViewMode("row")
  }

  function setStatusFilterTo(status: StatusFilter) {
    setStatusFilter(status)
  }

  function goToVendor(vendorId: string) {
    router.push("/vendors/" + vendorId)
  }

  function countByStatus(status: VendorStatus) {
    return vendors.filter(function matchesStatus(vendor) {
      return vendor.status === status
    }).length
  }

  // # 7.5 Drawer open and close handlers
  function openDrawer() {
    setIsDrawerOpen(true)
  }

  function closeDrawer() {
    setIsDrawerOpen(false)
    setSubmitError(null)
    setOpenInfoCode(null)
  }

  function resetForm() {
    setVendorName("")
    setVendorType("")
    setBusinessOwner("")
    setAnnualSpend("")
    setSelectedCategories([])
    setSystems([])
    setSystemInput("")
    setFiles([])
  }

  // # 7.6 Declared data category handlers
  function toggleCategoryMenu() {
    setIsCategoryMenuOpen(function flip(previous) {
      return !previous
    })
  }

  function addCategory(category: DataCategory) {
    setSelectedCategories(function appendCategory(previous) {
      if (previous.includes(category)) {
        return previous
      }
      return [...previous, category]
    })
    setIsCategoryMenuOpen(false)
  }

  function removeCategory(category: DataCategory) {
    setSelectedCategories(function withoutCategory(previous) {
      return previous.filter(function notRemoved(item) {
        return item !== category
      })
    })
  }

  // # 7.7 Declared systems handlers
  function addSystem() {
    const trimmed = systemInput.trim()
    if (trimmed.length === 0) {
      return
    }
    setSystems(function appendSystem(previous) {
      if (previous.includes(trimmed)) {
        return previous
      }
      return [...previous, trimmed]
    })
    setSystemInput("")
  }

  function removeSystem(system: string) {
    setSystems(function withoutSystem(previous) {
      return previous.filter(function notRemoved(item) {
        return item !== system
      })
    })
  }

  function handleSystemInputChange(event: ChangeEvent<HTMLInputElement>) {
    setSystemInput(event.target.value)
  }

  function handleSystemKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault()
      addSystem()
    }
  }

  // # 7.8 Document upload handlers
  function appendFiles(newFiles: File[]) {
    setFiles(function mergeFiles(previous) {
      const existingNames = previous.map(function getName(file) {
        return file.name
      })
      const uniqueNewFiles = newFiles.filter(function isUnique(file) {
        return !existingNames.includes(file.name)
      })
      return [...previous, ...uniqueNewFiles]
    })
  }

  function removeFile(fileName: string) {
    setFiles(function withoutFile(previous) {
      return previous.filter(function notRemoved(file) {
        return file.name !== fileName
      })
    })
  }

  function triggerFilePicker() {
    fileInputRef.current?.click()
  }

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) {
      appendFiles(Array.from(event.target.files))
    }
    event.target.value = ""
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    const dropped = Array.from(event.dataTransfer.files).filter(function isPdf(file) {
      return file.type === "application/pdf"
    })
    appendFiles(dropped)
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function toggleInfo(code: string) {
    setOpenInfoCode(function flip(previous) {
      return previous === code ? null : code
    })
  }

  function getFileForRequirement(code: string) {
    return files.find(function matches(file) {
      return detectDocumentType(file.name) === code
    })
  }

  // # 7.9 Form submission
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError(null)

    if (files.length === 0) {
      setSubmitError("Attach at least one supporting document before submitting.")
      return
    }

    setIsSubmitting(true)

    const formData = new FormData()
    formData.append("vendor_name", vendorName)
    formData.append("vendor_type", vendorType)
    formData.append("business_owner", businessOwner)
    if (annualSpend.trim().length > 0) {
      formData.append("annual_spend", annualSpend)
    }
    selectedCategories.forEach(function appendCategory(category) {
      formData.append("declared_data_categories", category)
    })
    if (systems.length > 0) {
      formData.append("declared_systems_accessed", systems.join(", "))
    }
    files.forEach(function appendDocument(file) {
      formData.append("documents", file)
    })

    // Cast required, the typed client expects a plain object but multipart
    // submissions are sent as FormData directly
    const result = await client.POST("/api/vendors/ingest", {
      body: formData as never,
    })

    setIsSubmitting(false)

    if (result.error) {
      setSubmitError("The registry rejected this submission. Check required fields and try again.")
      return
    }

    closeDrawer()
    resetForm()
    loadVendors()
  }

  // # 7.10 Derived values
  const filteredVendors = vendors.filter(function matchesFilter(vendor) {
    return statusFilter === "ALL" || vendor.status === statusFilter
  })

  const remainingCategories = DATA_CATEGORY_SEQUENCE.filter(function notSelected(category) {
    return !selectedCategories.includes(category)
  })

  // # 7.11 Render
  return (
    <div className="min-h-screen bg-background text-foreground max-w-7xl mx-auto">
      {/* Header */}
      <header className="border-b border-border">
        <div className="mx-auto flex  items-center justify-between gap-4 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-sm border border-foreground bg-foreground font-mono text-xs font-semibold text-background">
              VR
            </div>
            <div>
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Vendor Risk Management
              </p>
              <p className="text-sm text-muted-foreground">Compliance Clearance Desk</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              type="button"
              onClick={openDrawer}
              className="inline-flex items-center gap-2 rounded-sm bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Plus className="h-4 w-4" />
              Onboard Vendor
            </button>
          </div>
        </div>
      </header>

      {/* Hero, ledger framing and status filter strip */}
      <section className="border-b border-border bg-muted/40">
        <div className="mx-auto max-w-7xl px-6 py-10">
          <h1 className="font-mono text-2xl tracking-tight sm:text-3xl">Inspection Ledger</h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            Every vendor that touches company data passes through this checkpoint. Review
            clearance status below, or open a new intake to start an assessment.
          </p>

          <div className="mt-7 flex flex-wrap gap-2 items-center rounded-sm border border-border bg-background px-3 py-2">
            <button
              type="button"
              onClick={function selectAll() { setStatusFilterTo("ALL") }}
              className={
                "rounded-sm border px-3 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (statusFilter === "ALL"
                  ? "border-foreground bg-foreground text-background"
                  : "border-border bg-background hover:bg-muted")
              }
            >
              <p className="font-mono text-lg leading-none">{vendors.length}</p>
              <p className="mt-1 text-[11px] uppercase tracking-wide opacity-80">All vendors</p>
            </button>

            {STATUS_SEQUENCE.map(function renderStatusFilter(status) {
              const meta = STATUS_META[status]
              const isActive = statusFilter === status
              return (
                <button
                  key={status}
                  type="button"
                  onClick={function selectStatus() { setStatusFilterTo(status) }}
                  title={meta.description}
                  className={
                    "rounded-sm border px-3 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                    (isActive ? meta.classes + " ring-1 ring-inset ring-current" : "border-border bg-background hover:bg-muted")
                  }
                >
                  <p className="font-mono text-lg leading-none">{countByStatus(status)}</p>
                  <p className="mt-1 text-[11px] uppercase tracking-wide opacity-80">{meta.label}</p>
                </button>
              )
            })}
          </div>
        </div>
      </section>

      {/* Vendor registry */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            {filteredVendors.length} {pluralize(filteredVendors.length, "vendor")} on file
          </p>
          <div className="flex items-center gap-1 rounded-sm border border-border p-1">
            <button
              type="button"
              onClick={setGridView}
              aria-label="Grid view"
              className={
                "rounded-sm p-1.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (viewMode === "grid" ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted")
              }
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={setRowView}
              aria-label="Row view"
              className={
                "rounded-sm p-1.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (viewMode === "row" ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted")
              }
            >
              <List className="h-4 w-4" />
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center gap-2 rounded-sm border border-dashed border-border py-20 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading the registry
          </div>
        )}

        {!isLoading && loadError && (
          <div className="rounded-sm border border-rose-300 bg-rose-50 px-6 py-10 text-center">
            <p className="text-sm text-rose-700">{loadError}</p>
            <button
              type="button"
              onClick={loadVendors}
              className="mt-3 rounded-sm border border-rose-300 px-3 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-100"
            >
              Try again
            </button>
          </div>
        )}

        {!isLoading && !loadError && filteredVendors.length === 0 && (
          <div className="rounded-sm border border-dashed border-border px-6 py-20 text-center">
            <Building2 className="mx-auto h-8 w-8 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium">
              {vendors.length === 0 ? "No vendors on file yet" : "No vendors match this status"}
            </p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
              {vendors.length === 0
                ? "Onboard a vendor to start the compliance pipeline. Documents are reviewed automatically once submitted."
                : "Clear the filter above to see the rest of the registry."}
            </p>
            {vendors.length === 0 && (
              <button
                type="button"
                onClick={openDrawer}
                className="mt-5 inline-flex items-center gap-2 rounded-sm bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
              >
                <Plus className="h-4 w-4" />
                Onboard Vendor
              </button>
            )}
          </div>
        )}

        {!isLoading && !loadError && filteredVendors.length > 0 && viewMode === "grid" && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredVendors.map(function renderVendorCard(vendor) {
              const meta = STATUS_META[vendor.status] ?? STATUS_META.PENDING
              const delta = getRiskDelta(vendor.current_risk_score, vendor.previous_risk_score)
              return (
                <button
                  key={vendor.vendor_id}
                  type="button"
                  onClick={function selectVendor() { goToVendor(vendor.vendor_id) }}
                  className="group flex flex-col items-start rounded-sm border border-border bg-card p-4 text-left transition-colors hover:border-foreground/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <div className="flex w-full items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{vendor.vendor_name}</p>
                      <p className="truncate text-sm text-muted-foreground">{vendor.vendor_type}</p>
                    </div>
                    <span
                      className={
                        "shrink-0 -rotate-3 rounded-sm border px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-widest " +
                        meta.classes
                      }
                    >
                      {meta.label}
                    </span>
                  </div>

                  <div className="mt-4 flex w-full items-center justify-between border-t border-border pt-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Owner</p>
                      <p className="truncate text-sm">{vendor.business_owner}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Risk score</p>
                      <div className="flex items-center justify-end gap-1 font-mono text-sm">
                        {formatRiskScore(vendor.current_risk_score)}
                        {delta !== null && delta > 0 && <TrendingUp className="h-3.5 w-3.5 text-rose-600" />}
                        {delta !== null && delta < 0 && <TrendingDown className="h-3.5 w-3.5 text-emerald-600" />}
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 flex w-full items-center justify-between text-[11px] text-muted-foreground">
                    <span>Filed {formatDate(vendor.created_at)}</span>
                    <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </div>
                </button>
              )
            })}
          </div>
        )}

        {!isLoading && !loadError && filteredVendors.length > 0 && viewMode === "row" && (
          <div className="overflow-hidden rounded-sm border border-border">
            <div className="hidden border-b border-border bg-muted/40 px-4 py-2 text-[11px] uppercase tracking-wide text-muted-foreground sm:grid sm:grid-cols-12 sm:gap-4">
              <span className="sm:col-span-4">Vendor</span>
              <span className="sm:col-span-2">Owner</span>
              <span className="sm:col-span-2">Status</span>
              <span className="sm:col-span-2">Risk score</span>
              <span className="sm:col-span-2">Filed</span>
            </div>
            {filteredVendors.map(function renderVendorRow(vendor) {
              const meta = STATUS_META[vendor.status] ?? STATUS_META.PENDING
              const delta = getRiskDelta(vendor.current_risk_score, vendor.previous_risk_score)
              return (
                <button
                  key={vendor.vendor_id}
                  type="button"
                  onClick={function selectVendor() { goToVendor(vendor.vendor_id) }}
                  className="grid w-full grid-cols-1 gap-1 border-b border-border px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:grid-cols-12 sm:items-center sm:gap-4"
                >
                  <div className="min-w-0 sm:col-span-4">
                    <p className="truncate font-medium">{vendor.vendor_name}</p>
                    <p className="truncate text-sm text-muted-foreground">{vendor.vendor_type}</p>
                  </div>
                  <div className="truncate text-sm text-muted-foreground sm:col-span-2">
                    {vendor.business_owner}
                  </div>
                  <div className="sm:col-span-2">
                    <span
                      className={
                        "inline-block rounded-sm border px-2 py-0.5 font-mono text-[10px] font-bold uppercase tracking-widest " +
                        meta.classes
                      }
                    >
                      {meta.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 font-mono text-sm sm:col-span-2">
                    {formatRiskScore(vendor.current_risk_score)}
                    {delta !== null && delta > 0 && <TrendingUp className="h-3.5 w-3.5 text-rose-600" />}
                    {delta !== null && delta < 0 && <TrendingDown className="h-3.5 w-3.5 text-emerald-600" />}
                  </div>
                  <div className="flex items-center justify-between text-sm text-muted-foreground sm:col-span-2">
                    {formatDate(vendor.created_at)}
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 sm:hidden" />
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </main>

      {/* Intake drawer backdrop */}
      <div
        onClick={closeDrawer}
        aria-hidden="true"
        className={
          "fixed inset-0 z-40 bg-foreground/40 transition-opacity motion-reduce:transition-none " +
          (isDrawerOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0")
        }
      />

      {/* Intake drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="New vendor intake"
        className={
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background transition-transform motion-reduce:transition-none " +
          (isDrawerOpen ? "translate-x-0" : "translate-x-full")
        }
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">New Intake</p>
            <p className="text-sm font-medium">Vendor Onboarding</p>
          </div>
          <button
            type="button"
            onClick={closeDrawer}
            aria-label="Close"
            className="rounded-sm p-1.5 text-muted-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-y-auto">
          <div className="flex-1 space-y-8 px-5 py-6">
            {/* Identity */}
            <fieldset>
              <legend className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Vendor Identity
              </legend>
              <div className="mt-3 space-y-3">
                <div>
                  <label htmlFor="vendor_name" className="text-sm font-medium">
                    Vendor name <span className="text-rose-600">*</span>
                  </label>
                  <input
                    id="vendor_name"
                    type="text"
                    required
                    value={vendorName}
                    onChange={function onVendorName(event) { setVendorName(event.target.value) }}
                    placeholder="Official legal corporate name"
                    className="mt-1 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <div>
                  <label htmlFor="vendor_type" className="text-sm font-medium">
                    Vendor type <span className="text-rose-600">*</span>
                  </label>
                  <input
                    id="vendor_type"
                    type="text"
                    required
                    value={vendorType}
                    onChange={function onVendorType(event) { setVendorType(event.target.value) }}
                    placeholder="e.g. Cloud Storage Provider"
                    className="mt-1 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <div>
                  <label htmlFor="business_owner" className="text-sm font-medium">
                    Business owner <span className="text-rose-600">*</span>
                  </label>
                  <input
                    id="business_owner"
                    type="text"
                    required
                    value={businessOwner}
                    onChange={function onBusinessOwner(event) { setBusinessOwner(event.target.value) }}
                    placeholder="Internal manager overseeing this vendor"
                    className="mt-1 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <div>
                  <label htmlFor="annual_spend" className="text-sm font-medium">
                    Annual spend
                  </label>
                  <input
                    id="annual_spend"
                    type="number"
                    step="0.01"
                    min="0"
                    value={annualSpend}
                    onChange={function onAnnualSpend(event) { setAnnualSpend(event.target.value) }}
                    placeholder="Optional, in USD"
                    className="mt-1 w-full rounded-sm border border-border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
              </div>
            </fieldset>

            {/* Declared scope */}
            <fieldset>
              <legend className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Declared Scope
              </legend>

              <div className="mt-3">
                <p className="text-sm font-medium">Data categories</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  What categories of data will this vendor be exposed to.
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {selectedCategories.map(function renderCategoryChip(category) {
                    return (
                      <span
                        key={category}
                        title={DATA_CATEGORY_META[category]}
                        className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-muted px-2 py-1 text-xs"
                      >
                        {category}
                        <button
                          type="button"
                          onClick={function onRemove() { removeCategory(category) }}
                          aria-label={"Remove " + category}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    )
                  })}

                  <div className="relative">
                    <button
                      type="button"
                      onClick={toggleCategoryMenu}
                      disabled={remainingCategories.length === 0}
                      className="inline-flex items-center gap-1 rounded-sm border border-dashed border-border px-2 py-1 text-xs text-muted-foreground hover:bg-muted disabled:opacity-40"
                    >
                      <Plus className="h-3 w-3" />
                      Add
                    </button>

                    {isCategoryMenuOpen && remainingCategories.length > 0 && (
                      <div className="absolute left-0 z-10 mt-1 w-64 rounded-sm border border-border bg-card p-1">
                        {remainingCategories.map(function renderCategoryOption(category) {
                          return (
                            <button
                              key={category}
                              type="button"
                              onClick={function onAdd() { addCategory(category) }}
                              className="block w-full rounded-sm px-2 py-1.5 text-left text-xs hover:bg-muted"
                            >
                              <span className="font-mono">{category}</span>
                              <span className="block text-muted-foreground">
                                {DATA_CATEGORY_META[category]}
                              </span>
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-5">
                <p className="text-sm font-medium">Systems accessed</p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Internal systems this vendor will read or write to, for example prod-db-01.
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {systems.map(function renderSystemChip(system) {
                    return (
                      <span
                        key={system}
                        className="inline-flex items-center gap-1.5 rounded-sm border border-border bg-muted px-2 py-1 text-xs"
                      >
                        {system}
                        <button
                          type="button"
                          onClick={function onRemove() { removeSystem(system) }}
                          aria-label={"Remove " + system}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    )
                  })}
                </div>
                <div className="mt-2 flex gap-1.5">
                  <input
                    type="text"
                    value={systemInput}
                    onChange={handleSystemInputChange}
                    onKeyDown={handleSystemKeyDown}
                    placeholder="System name, then press enter"
                    className="flex-1 rounded-sm border border-border bg-background px-3 py-1.5 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <button
                    type="button"
                    onClick={addSystem}
                    className="rounded-sm border border-dashed border-border px-2 text-muted-foreground hover:bg-muted"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </fieldset>

            {/* Document intake */}
            <fieldset>
              <legend className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Document Intake
              </legend>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Upload supporting PDFs together. File names must contain a structural keyword so
                each one is sorted correctly, see the checklist below.
              </p>

              <div className="mt-3 space-y-1.5">
                {DOCUMENT_REQUIREMENTS.map(function renderRequirement(requirement) {
                  const matchedFile = getFileForRequirement(requirement.code)
                  return (
                    <div
                      key={requirement.code}
                      className="rounded-sm border border-border px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={
                              "h-1.5 w-1.5 rounded-full " +
                              (matchedFile ? "bg-emerald-600" : "bg-muted-foreground/40")
                            }
                          />
                          <span className="text-sm">{requirement.label}</span>
                        </div>
                        <div className="relative flex items-center gap-2">
                          <span className="text-[11px] text-muted-foreground">
                            {matchedFile ? "Attached" : "Missing"}
                          </span>
                          <button
                            type="button"
                            onClick={function onToggle() { toggleInfo(requirement.code) }}
                            aria-label={"About " + requirement.label}
                            className="rounded-sm p-0.5 text-muted-foreground hover:bg-muted"
                          >
                            <MoreVertical className="h-3.5 w-3.5" />
                          </button>
                          {openInfoCode === requirement.code && (
                            <div className="absolute right-0 top-6 z-10 w-56 rounded-sm border border-border bg-card p-2 text-xs">
                              <p>{requirement.description}</p>
                              <p className="mt-1 text-muted-foreground">{requirement.keywordHint}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={
                  "mt-3 flex flex-col items-center justify-center rounded-sm border border-dashed px-4 py-8 text-center transition-colors " +
                  (isDragging ? "border-foreground bg-muted/60" : "border-border")
                }
              >
                <Upload className="h-5 w-5 text-muted-foreground" />
                <p className="mt-2 text-sm">Drag PDFs here, or</p>
                <button
                  type="button"
                  onClick={triggerFilePicker}
                  className="mt-1 text-sm font-medium underline underline-offset-2"
                >
                  browse files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </div>

              {files.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {files.map(function renderFileRow(file) {
                    const detected = detectDocumentType(file.name)
                    const requirement = DOCUMENT_REQUIREMENTS.find(function matches(item) {
                      return item.code === detected
                    })
                    return (
                      <li
                        key={file.name}
                        className="flex items-center justify-between gap-2 rounded-sm border border-border px-3 py-2 text-sm"
                      >
                        <div className="flex min-w-0 items-center gap-2">
                          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                          <div className="min-w-0">
                            <p className="truncate">{file.name}</p>
                            <p
                              className={
                                "text-[11px] " +
                                (requirement ? "text-emerald-700" : "text-amber-700")
                              }
                            >
                              {requirement ? requirement.label : "Unrecognized, rename to include a structural keyword"}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={function onRemove() { removeFile(file.name) }}
                          aria-label={"Remove " + file.name}
                          className="shrink-0 rounded-sm p-1 text-muted-foreground hover:bg-muted"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </li>
                    )
                  })}
                </ul>
              )}
            </fieldset>
          </div>

          <div className="border-t border-border px-5 py-4">
            {submitError && (
              <p className="mb-3 rounded-sm border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                {submitError}
              </p>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-sm bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isSubmitting ? "Submitting" : "Submit for assessment"}
            </button>
            <p className="mt-2 text-center text-[11px] text-muted-foreground">
              Documents are queued for automatic review once submitted.
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}