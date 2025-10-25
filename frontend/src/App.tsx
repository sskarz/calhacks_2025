import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { clsx } from "clsx";
import {
  STOREFRONTS,
  StorefrontId,
  storefrontBadgeStyles,
  storefrontAccent
} from "./lib/storefronts";
import { formatCurrency, formatRelativeDate, generateId } from "./lib/utils";
import type { ListingItem, ListingStatus } from "./lib/types";
import {api, wsManager} from "./lib/api";

interface FormState {
  title: string;
  description: string;
  price: string;
  status: "listed" | "sold" | "pending";
  platform: "ebay" | "etsy" | "shopify" | "amazon";
  quantity: number;
  imagePreview: string | null;
}

const DEFAULT_FORM: FormState = {
  title: "",
  description: "",
  price: "",
  status: "listed",
  platform: "ebay",
  quantity: 1,
  imagePreview: null
};

const SAMPLE_ITEMS: ListingItem[] = [
  {
    id: "s1",
    title: "Vintage Polaroid Camera",
    description: "Refurbished 1980s instant camera with new film pack.",
    platform: "etsy",
    price: 129.99,
    status: "listed",
    quantity: 2,
    createdAt: "2024-07-11T09:42:00Z",
    updatedAt: "2024-07-18T15:12:00Z",
    imageSrc:
      "https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "s2",
    title: "Hand-poured Soy Candle Trio",
    description: "Set of three seasonal scents with reusable jars.",
    platform: "etsy",
    price: 45.0,
    status: "sold",
    quantity: 0,
    createdAt: "2024-07-14T12:03:00Z",
    updatedAt: "2024-07-19T08:45:00Z",
    imageSrc:
      "https://images.unsplash.com/photo-1512418490979-92798cec1380?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "s3",
    title: "Refurbished MacBook Air 13\"",
    description:
      "M1 chip, 16GB RAM, professionally serviced with 30-day warranty.",
    platform: "ebay",
    price: 849.99,
    status: "listed",
    quantity: 3,
    createdAt: "2024-07-16T18:26:00Z",
    updatedAt: "2024-07-19T08:00:00Z",
    imageSrc:
      "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=600&q=80"
  },
  {
    id: "s4",
    title: "Minimalist Backpack",
    description: "Weather-resistant canvas backpack with laptop sleeve.",
    platform: "shopify",
    price: 98.5,
    status: "pending",
    quantity: 15,
    createdAt: "2024-07-17T10:15:00Z",
    updatedAt: "2024-07-17T10:15:00Z",
    imageSrc:
      "https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?auto=format&fit=crop&w=600&q=80"
  }
];

const ACTIVITY_FEED = [
  {
    id: "a1",
    message: "Synced inventory adjustments from Shopify",
    timestamp: "2024-07-19T11:32:00Z",
    platform: "shopify" as StorefrontId
  },
  {
    id: "a2",
    message: "Auto-relisted sold candle set on Etsy",
    timestamp: "2024-07-19T10:18:00Z",
    platform: "etsy" as StorefrontId
  },
  {
    id: "a3",
    message: "Pushed new laptop listing to eBay in electronics category",
    timestamp: "2024-07-19T08:02:00Z",
    platform: "ebay" as StorefrontId
  }
];

const statusLabel: Record<ListingStatus, string> = {
  listed: "Live",
  pending: "Pending approval",
  sold: "Sold"
};

const statusClasses: Record<ListingStatus, string> = {
  listed: "bg-blue-100 text-blue-700 border border-blue-200",
  pending: "bg-amber-100 text-amber-700 border border-amber-200",
  sold: "bg-emerald-100 text-emerald-700 border border-emerald-200"
};

const platformFilters: Array<{ id: "all" | StorefrontId; label: string }> = [
  { id: "all", label: "All storefronts" },
  { id: "ebay", label: "eBay" },
  { id: "etsy", label: "Etsy" },
  { id: "shopify", label: "Shopify" }
];

function App() {
  const [items, setItems] = useState<ListingItem[]>(SAMPLE_ITEMS);
  const [formState, setFormState] = useState<FormState>(DEFAULT_FORM);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState<
    "all" | StorefrontId
  >("all");
  const [statusFilter, setStatusFilter] = useState<"all" | ListingStatus>("all");
  const [autoRelist, setAutoRelist] = useState(true);
  const [inventorySync, setInventorySync] = useState(true);
  const [smartPricing, setSmartPricing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    wsManager.connect(
      (updatedItems) => setItems(updatedItems),
      (error) => console.error('WS error:', error)
    );

    return () => wsManager.disconnect();
  }, []);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch =
        !search ||
        item.title.toLowerCase().includes(search.toLowerCase()) ||
        item.description.toLowerCase().includes(search.toLowerCase());

      const matchesPlatform =
        platformFilter === "all" || item.platform === platformFilter;

      const matchesStatus = statusFilter === "all" || item.status === statusFilter;

      return matchesSearch && matchesPlatform && matchesStatus;
    });
  }, [items, search, platformFilter, statusFilter]);

  const metrics = useMemo(() => {
    const total = items.length;
    const soldCount = items.filter((item) => item.status === "sold").length;
    const listedCount = items.filter((item) => item.status === "listed").length;
    const pendingCount = items.filter((item) => item.status === "pending").length;
    const revenue = items
      .filter((item) => item.status === "sold")
      .reduce((sum, item) => sum + item.price, 0);

    const platformBreakdown = items.reduce<Record<StorefrontId, number>>(
      (acc, item) => {
        acc[item.platform] = (acc[item.platform] ?? 0) + 1;
        return acc;
      },
      { ebay: 0, etsy: 0, shopify: 0 }
    );

    return {
      total,
      soldCount,
      listedCount,
      pendingCount,
      revenue,
      platformBreakdown
    };
  }, [items]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setFormState((prev) => ({ ...prev, imagePreview: null }));
      return;
    }

    const preview = URL.createObjectURL(file);
    setFormState((prev) => ({
      ...prev,
      imagePreview: preview
    }));
  };

  const resetForm = () => {
    setFormState((prev) => ({
      ...DEFAULT_FORM,
      platform: prev.platform,
      status: prev.status
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.imagePreview) {
      alert("Please upload an item image before listing.");
      return;
    }
    if (!formState.title || !formState.price) {
      alert("Title and price are required fields.");
      return;
    }

    setIsSubmitting(true);
    try {
      // Convert blob URL to actual blob
      const response = await fetch(formState.imagePreview);
      const blob = await response.blob();

      // Create FormData to send multipart
      const formData = new FormData();
      formData.append("title", formState.title);
      formData.append("description", formState.description);
      formData.append("platform", formState.platform);
      formData.append("price", String(formState.price));
      formData.append("status", formState.status);
      formData.append("quantity", String(formState.quantity));
      formData.append("image", blob, "item-image.jpg");

      await api.post("/add_item", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });

      resetForm();
    } catch (error) {
      alert("Failed to add item. Please try again.");
      console.error('Error adding item:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <TopNav />
      <main className="mx-auto max-w-7xl px-6 py-8">
        <section className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr,1fr]">
          <ListingWorkflowCard
            formState={formState}
            onFormChange={setFormState}
            onSubmit={handleSubmit}
            onFileChange={handleFileChange}
            isSubmitting={isSubmitting}
            autoRelist={autoRelist}
            setAutoRelist={setAutoRelist}
            inventorySync={inventorySync}
            setInventorySync={setInventorySync}
            smartPricing={smartPricing}
            setSmartPricing={setSmartPricing}
          />
          <SidePanel
            metrics={metrics}
            autoRelist={autoRelist}
            inventorySync={inventorySync}
            smartPricing={smartPricing}
          />
        </section>

        <section className="mt-10 space-y-6">
          <FilterBar
            search={search}
            onSearchChange={setSearch}
            platformFilter={platformFilter}
            onPlatformFilterChange={setPlatformFilter}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
          />
          <InventoryTable items={filteredItems} />
        </section>
      </main>
    </div>
  );
}

function TopNav() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Omnichannel Commerce Console
          </p>
          <h1 className="mt-1 text-xl font-semibold text-slate-800">
            Agent Listing Control Center
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-800">
            Export CSV
          </button>
          <button className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700">
            Sync All Channels
          </button>
          <span className="h-8 w-8 rounded-full bg-slate-200" aria-hidden />
        </div>
      </div>
    </header>
  );
}

interface ListingWorkflowCardProps {
  formState: FormState;
  onFormChange: (updater: FormState | ((prev: FormState) => FormState)) => void;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isSubmitting: boolean;
  autoRelist: boolean;
  setAutoRelist: (value: boolean) => void;
  inventorySync: boolean;
  setInventorySync: (value: boolean) => void;
  smartPricing: boolean;
  setSmartPricing: (value: boolean) => void;
}

function ListingWorkflowCard({
  formState,
  onFormChange,
  onFileChange,
  onSubmit,
  isSubmitting,
  autoRelist,
  setAutoRelist,
  inventorySync,
  setInventorySync,
  smartPricing,
  setSmartPricing
}: ListingWorkflowCardProps) {
  const handleFieldChange = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    onFormChange((prev) => ({ ...prev, [key]: value }));

  const steps = [
    {
      title: "Upload item media",
      description: "High quality images improve conversion by 43%.",
      isComplete: Boolean(formState.imagePreview),
      action: (
        <UploadDropzone
          imagePreview={formState.imagePreview ?? undefined}
          onFileChange={onFileChange}
        />
      )
    },
    {
      title: "Enrich listing details",
      description: "Set marketplace-ready pricing and merchandising data.",
      isComplete: Boolean(formState.title && formState.price),
      action: (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700">
              Title
            </label>
            <input
              type="text"
              value={formState.title}
              onChange={(event) => handleFieldChange("title", event.target.value)}
              placeholder="What are you listing?"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700">
              Description
            </label>
            <textarea
              value={formState.description}
              onChange={(event) =>
                handleFieldChange("description", event.target.value)
              }
              rows={3}
              placeholder="Include details the agents should highlight."
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Price (USD)
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={formState.price}
              onChange={(event) => handleFieldChange("price", event.target.value)}
              placeholder="0.00"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Quantity in stock
            </label>
            <input
              type="number"
              min={0}
              value={formState.quantity}
              onChange={(event) =>
                handleFieldChange("quantity", Number(event.target.value))
              }
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              Listing status
            </label>
            <select
              value={formState.status}
              onChange={(event) =>
                handleFieldChange("status", event.target.value as ListingStatus)
              }
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            >
              <option value="listed">Live</option>
              <option value="pending">Pending</option>
              <option value="sold">Sold</option>
            </select>
          </div>
        </div>
      )
    },
    {
      title: "Select storefronts & automations",
      description: "Assign the optimal channel strategy for this item.",
      isComplete: Boolean(formState.platform),
      action: (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {(Object.keys(STOREFRONTS) as StorefrontId[]).map((platform) => {
              const detail = STOREFRONTS[platform];
              const isActive = formState.platform === platform;
              return (
                <button
                  key={platform}
                  type="button"
                  onClick={() => handleFieldChange("platform", platform)}
                  className={clsx(
                    "rounded-xl border px-4 py-3 text-left shadow-sm transition focus:outline-none focus:ring-2 focus:ring-slate-900/10",
                    isActive
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                  )}
                >
                  <p className="text-sm font-semibold">{detail.label}</p>
                  <p
                    className={clsx(
                      "mt-1 text-xs leading-relaxed",
                      isActive ? "text-slate-100" : "text-slate-500"
                    )}
                  >
                    {detail.description}
                  </p>
                </button>
              );
            })}
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <AutomationToggle
              label="Auto-relist sold out inventory"
              description="Agents will duplicate listings once supply replenishes."
              checked={autoRelist}
              onChange={setAutoRelist}
            />
            <AutomationToggle
              label="Inventory sync"
              description="Lock stock counts across channels to avoid oversell."
              checked={inventorySync}
              onChange={setInventorySync}
            />
            <AutomationToggle
              label="Smart pricing"
              description="Benchmark against competitors before publishing."
              checked={smartPricing}
              onChange={setSmartPricing}
            />
          </div>
        </div>
      )
    }
  ];

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <div className="border-b border-slate-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Launch a new listing
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Flow through the agent-ready checklist to push an item everywhere at
          once.
        </p>
      </div>

      <div className="space-y-0.5 px-6 py-4">
        {steps.map((step, index) => (
          <div
            key={step.title}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50/60 p-5 transition hover:border-slate-300 hover:shadow-sm md:flex-row md:items-start"
          >
            <div className="flex w-full max-w-[220px] items-start gap-3">
              <div
                className={clsx(
                  "flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold",
                  step.isComplete
                    ? "border-emerald-200 bg-emerald-100 text-emerald-700"
                    : "border-slate-200 bg-white text-slate-600"
                )}
              >
                {index + 1}
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">
                  {step.title}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">
                  {step.description}
                </p>
              </div>
            </div>
            <div className="flex-1">{step.action}</div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-6 py-4">
        <p className="text-sm text-slate-500">
          Publishing as soon as the storefront agent confirms inventory & policy
          compliance.
        </p>
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 disabled:pointer-events-none disabled:opacity-50"
        >
          {isSubmitting ? "Publishing..." : "Send to agents"}
        </button>
      </div>
    </form>
  );
}

function UploadDropzone({
  imagePreview,
  onFileChange
}: {
  imagePreview?: string;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <label className="flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white text-center transition hover:border-slate-400 hover:bg-slate-50">
      {imagePreview ? (
        <img
          src={imagePreview}
          alt="Preview"
          className="h-full w-full rounded-xl object-cover"
        />
      ) : (
          <div className="flex flex-col items-center gap-2 px-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
              <svg
                aria-hidden="true"
                className="h-5 w-5 text-slate-500"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M4 7a2 2 0 0 1 2-2h2.2a1 1 0 0 0 .95-.68l.3-.9A1 1 0 0 1 10.4 3h3.2a1 1 0 0 1 .95.63l.3.9a1 1 0 0 0 .95.67H18a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
                <circle cx="12" cy="12" r="3.5" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Drop image or browse files
            </p>
          <p className="text-xs text-slate-500">
            Support for PNG, JPG, and WEBP up to 10 MB.
          </p>
        </div>
      )}
      <input
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={onFileChange}
        className="hidden"
      />
    </label>
  );
}

function AutomationToggle({
  label,
  description,
  checked,
  onChange
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer flex-col gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:border-slate-300 hover:bg-slate-50">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-800">{label}</span>
        <span
          className={clsx(
            "inline-flex h-6 w-11 items-center rounded-full border px-0.5 transition",
            checked
              ? "border-slate-900 bg-slate-900"
              : "border-slate-200 bg-slate-200"
          )}
        >
          <span
            className={clsx(
              "h-5 w-5 rounded-full bg-white shadow transition",
              checked ? "translate-x-5" : "translate-x-0"
            )}
          />
        </span>
      </div>
      <span className="text-xs leading-relaxed text-slate-500">{description}</span>
      <input
        type="checkbox"
        className="hidden"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}

function SidePanel({
  metrics,
  autoRelist,
  inventorySync,
  smartPricing
}: {
  metrics: {
    total: number;
    soldCount: number;
    listedCount: number;
    pendingCount: number;
    revenue: number;
    platformBreakdown: Record<StorefrontId, number>;
  };
  autoRelist: boolean;
  inventorySync: boolean;
  smartPricing: boolean;
}) {
  const fulfillmentScore = Math.min(
    100,
    metrics.listedCount * 5 + metrics.soldCount * 15 + (autoRelist ? 10 : 0)
  );

  return (
    <aside className="flex h-full flex-col gap-5 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <section>
        <h3 className="text-sm font-semibold text-slate-800">
          Live channel coverage
        </h3>
        <p className="mt-2 text-xs text-slate-500">
          Agents keep your inventory consistent and competitively priced across
          every storefront.
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <MetricCard label="Active listings" value={metrics.listedCount} />
          <MetricCard label="Sold (24h)" value={metrics.soldCount} />
          <MetricCard label="Pending review" value={metrics.pendingCount} />
          <MetricCard label="Revenue to date" value={formatCurrency(metrics.revenue)} />
        </dl>
      </section>

      <section className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Channel mix
        </p>
        <div className="mt-3 space-y-2">
          {(Object.keys(STOREFRONTS) as StorefrontId[]).map((platform) => (
            <div key={platform} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    "flex h-2 w-8 rounded-full",
                    storefrontAccent(platform).replace("text", "bg")
                  )}
                />
                <span className="font-medium text-slate-700">
                  {STOREFRONTS[platform].label}
                </span>
              </div>
              <span className="text-slate-500">
                {metrics.platformBreakdown[platform]} listings
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-slate-800">Agent activity</h3>
        <ul className="mt-3 space-y-3 text-sm text-slate-600">
          {ACTIVITY_FEED.map((entry) => (
            <li
              key={entry.id}
              className="flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3"
            >
              <span
                className={clsx(
                  "mt-0.5 inline-flex h-2.5 w-2.5 rounded-full",
                  storefrontAccent(entry.platform).replace("text", "bg")
                )}
              />
              <div>
                <p>{entry.message}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {formatRelativeDate(entry.timestamp)}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-auto rounded-xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Health score
        </p>
        <p className="mt-2 text-3xl font-semibold text-slate-800">
          {fulfillmentScore}%
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Keep automation toggles on to drive omni-channel coverage.
        </p>
        <div className="mt-3 h-2 w-full rounded-full bg-slate-200">
          <div
            className="h-2 rounded-full bg-slate-900 transition-all"
            style={{ width: `${fulfillmentScore}%` }}
          />
        </div>
      </section>
    </aside>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-1 text-sm font-semibold text-slate-800">{value}</dd>
    </div>
  );
}

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  platformFilter: "all" | StorefrontId;
  onPlatformFilterChange: (value: "all" | StorefrontId) => void;
  statusFilter: "all" | ListingStatus;
  onStatusFilterChange: (value: "all" | ListingStatus) => void;
}

function FilterBar({
  search,
  onSearchChange,
  platformFilter,
  onPlatformFilterChange,
  statusFilter,
  onStatusFilterChange
}: FilterBarProps) {
  const statusFilters: Array<{
    id: "all" | ListingStatus;
    label: string;
    badge: ListingStatus | "all";
  }> = [
    { id: "all", label: "All statuses", badge: "all" },
    { id: "listed", label: "Live", badge: "listed" },
    { id: "pending", label: "Pending", badge: "pending" },
    { id: "sold", label: "Sold", badge: "sold" }
  ];

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-1 min-w-[220px] items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 shadow-sm">
        <span className="text-lg text-slate-400">&#128269;</span>
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search by title, SKU, or tag"
          className="w-full border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
        />
      </div>
      <div className="flex flex-wrap gap-2">
        {platformFilters.map((filter) => {
          const isActive = platformFilter === filter.id;
          return (
            <button
              key={filter.id}
              type="button"
              onClick={() => onPlatformFilterChange(filter.id)}
              className={clsx(
                "rounded-lg border px-3 py-2 text-sm font-medium shadow-sm transition",
                isActive
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              {filter.label}
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-2">
        {statusFilters.map((filter) => {
          const isActive = statusFilter === filter.id;
          return (
            <button
              key={filter.id}
              type="button"
              onClick={() => onStatusFilterChange(filter.id)}
              className={clsx(
                "rounded-lg border px-3 py-2 text-sm font-medium shadow-sm transition",
                isActive
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              {filter.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function InventoryTable({ items }: { items: ListingItem[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Listing queue</h2>
          <p className="mt-1 text-sm text-slate-500">
            Track agent progress and outcomes across every storefront in real time.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-800">
            View kanban
          </button>
          <button className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-800">
            Download report
          </button>
        </div>
      </div>
      <table className="min-w-full divide-y divide-slate-200 text-left">
        <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
          <tr>
            <th className="px-6 py-3 font-semibold">Item</th>
            <th className="px-6 py-3 font-semibold">Storefront</th>
            <th className="px-6 py-3 font-semibold">Status</th>
            <th className="px-6 py-3 font-semibold">Price</th>
            <th className="px-6 py-3 font-semibold">Updated</th>
            <th className="px-6 py-3 font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 text-sm text-slate-700">
          {items.map((item) => (
            <tr
              key={item.id}
              className={clsx(
                "border-l-4 transition hover:bg-slate-50",
                STOREFRONTS[item.platform].borderStrong
              )}
            >
              <td className="flex items-center gap-3 px-6 py-4">
                <img
                  src={item.imageSrc}
                  alt={item.title}
                  className="h-14 w-14 flex-shrink-0 rounded-lg object-cover"
                />
                <div>
                  <p className="font-semibold text-slate-900">{item.title}</p>
                  <p className="max-w-md truncate text-xs text-slate-500">
                    {item.description}
                  </p>
                </div>
              </td>
              <td className="px-6 py-4">
                <span
                  className={clsx(
                    "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold",
                    storefrontBadgeStyles(item.platform)
                  )}
                >
                  {STOREFRONTS[item.platform].label}
                </span>
              </td>
              <td className="px-6 py-4">
                <span
                  className={clsx(
                    "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
                    statusClasses[item.status]
                  )}
                >
                  {statusLabel[item.status]}
                </span>
              </td>
              <td className="px-6 py-4 font-medium">
                {formatCurrency(item.price)}
                {item.quantity ? (
                  <span className="ml-2 text-xs text-slate-500">
                    Stock: {item.quantity}
                  </span>
                ) : null}
              </td>
              <td className="px-6 py-4 text-xs text-slate-500">
                {formatRelativeDate(item.updatedAt)}
              </td>
              <td className="px-6 py-4">
                <div className="flex gap-2">
                  <button className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-800">
                    Duplicate
                  </button>
                  <button className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-800">
                    Pause
                  </button>
                </div>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={6} className="px-6 py-12 text-center text-sm text-slate-500">
                No listings match the current filters. Adjust search or add a new
                listing above.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default App;
