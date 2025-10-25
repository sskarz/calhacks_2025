import type { StorefrontId } from "./storefronts";

export type ListingStatus = "listed" | "sold" | "pending";

export interface ListingItem {
  id: string;
  title: string;
  description: string;
  platform: StorefrontId;
  price: number;
  status: ListingStatus;
  quantity: number;
  createdAt: string;
  updatedAt: string;
  imageSrc: string;
  sku?: string;
  tags?: string[];
}
