import { clsx } from "clsx";

export type StorefrontId = "ebay" | "etsy" | "shopify";

export const STOREFRONTS: Record<
  StorefrontId,
  {
    id: StorefrontId;
    label: string;
    description: string;
    accent: string;
    bg: string;
    text: string;
    border: string;
    borderStrong: string;
  }
> = {
  ebay: {
    id: "ebay",
    label: "eBay",
    description: "Auction-style or fixed price listings with global reach.",
    accent: "text-platform-ebay",
    bg: "bg-blue-50",
    text: "text-platform-ebay",
    border: "border-blue-200",
    borderStrong: "border-platform-ebay"
  },
  etsy: {
    id: "etsy",
    label: "Etsy",
    description: "Handmade, vintage, and custom goods marketplace.",
    accent: "text-platform-etsy",
    bg: "bg-orange-50",
    text: "text-platform-etsy",
    border: "border-orange-200",
    borderStrong: "border-platform-etsy"
  },
  shopify: {
    id: "shopify",
    label: "Shopify",
    description: "Direct-to-consumer storefront with customizable themes.",
    accent: "text-platform-shopify",
    bg: "bg-emerald-50",
    text: "text-platform-shopify",
    border: "border-emerald-200",
    borderStrong: "border-platform-shopify"
  }
};

export const storefrontAccent = (id: StorefrontId) =>
  clsx(STOREFRONTS[id]?.accent ?? "text-slate-600");

export const storefrontBadgeStyles = (id: StorefrontId) =>
  ({
    ebay: "bg-blue-100 text-platform-ebay border border-blue-200",
    etsy: "bg-orange-100 text-platform-etsy border border-orange-200",
    shopify: "bg-emerald-100 text-platform-shopify border border-emerald-200"
  })[id] ?? "bg-slate-100 text-slate-600 border border-slate-200";
