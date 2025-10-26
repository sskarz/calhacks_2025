export type Platform = "etsy" | "ebay";
export type ListingStatus = "draft" | "pending" | "live" | "sold" | "failed";

export interface Listing {
  id: string;
  name: string;
  price: string;
  description: string;
  category: string;
  condition: string;
  imageUrl: string;
  platform: Platform;
  status: ListingStatus;
  createdAt: Date;
  updatedAt: Date;
}
