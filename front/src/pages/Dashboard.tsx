import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Plus, Trash2, Eye } from "lucide-react";
import type { Listing, ListingStatus } from "@/types/listing";
import { toast } from "sonner";
import { wsManager } from "@/lib/api";

const statusConfig: Record<ListingStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
  draft: { label: "Draft", variant: "secondary" },
  pending: { label: "Pending", variant: "outline" },
  live: { label: "Live", variant: "default" },
  sold: { label: "Sold", variant: "default" },
  failed: { label: "Failed", variant: "destructive" },
};

// Map backend response to Listing type
function mapBackendToListing(item: any): Listing {
  // Normalize status to valid values
  let status = (item.status || "draft").toLowerCase() as ListingStatus;
  const validStatuses: ListingStatus[] = ['draft', 'pending', 'live', 'sold', 'failed'];
  if (!validStatuses.includes(status)) {
    status = 'draft'; // Default to draft if invalid
  }

  return {
    id: item.id.toString(),
    name: item.title,
    description: item.description,
    price: item.price,
    platform: item.platform.toLowerCase(),
    status,
    category: item.category || "uncategorized",
    condition: item.condition || "new",
    createdAt: item.createdAt ?? new Date().toISOString(),
    updatedAt: item.updatedAt ?? new Date().toISOString(),
    imageUrl: item.imageSrc ? `data:image/png;base64,${item.imageSrc}` : "",
  };
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [listings, setListings] = useState<Listing[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Load initial listings from localStorage
    const storedListings = JSON.parse(localStorage.getItem("listings") || "[]");
    const mappedListings = storedListings.map(mapBackendToListing);
    setListings(mappedListings);

    // Connect to API polling
    wsManager.connect(
      (data) => {
        // Update listings with incoming data from backend
        if (Array.isArray(data)) {
          const mappedListings = data.map(mapBackendToListing);
          setListings(mappedListings);
          localStorage.setItem("listings", JSON.stringify(data));
        } else if (data.listings && Array.isArray(data.listings)) {
          const mappedListings = data.listings.map(mapBackendToListing);
          setListings(mappedListings);
          localStorage.setItem("listings", JSON.stringify(data.listings));
        }
        setIsConnected(true);
      },
      (error) => {
        console.error("API error:", error);
        setIsConnected(false);
      }
    );

    return () => {
      wsManager.disconnect();
    };
  }, []);

  const handleDelete = (id: string) => {
    const updatedListings = listings.filter((listing) => listing.id !== id);
    setListings(updatedListings);
    toast.success("Listing deleted");
  };

  const getPlatformColor = (platform: string) => {
    const platformLower = platform.toLowerCase();
    return platformLower === "etsy" || platformLower === "tetsy"
      ? "bg-gradient-to-r from-orange-500 to-orange-600" 
      : "bg-gradient-to-r from-blue-500 to-blue-600";
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold mb-2">Listings Dashboard</h1>
            <p className="text-muted-foreground">
              Manage all your marketplace listings in one place
              {isConnected && <span className="ml-2 text-green-500">● Connected</span>}
              {!isConnected && <span className="ml-2 text-red-500">● Disconnected</span>}
            </p>
          </div>
          <Button
            onClick={() => navigate("/create")}
            size="lg"
            className="bg-accent hover:bg-accent/90"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Listing
          </Button>
        </div>

        {listings.length === 0 ? (
          <Card className="p-12 text-center">
            <div className="max-w-md mx-auto">
              <h3 className="text-2xl font-semibold mb-4">No listings yet</h3>
              <p className="text-muted-foreground mb-6">
                Create your first listing to start selling on Etsy and eBay
              </p>
              <Button
                onClick={() => navigate("/create")}
                size="lg"
                className="bg-accent hover:bg-accent/90"
              >
                <Plus className="w-5 h-5 mr-2" />
                Create Your First Listing
              </Button>
            </div>
          </Card>
        ) : (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">Image</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Platform</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {listings.map((listing) => (
                  <TableRow key={listing.id}>
                    <TableCell>
                      <img
                        src={listing.imageUrl}
                        alt={listing.name}
                        className="w-16 h-16 object-cover rounded-lg bg-muted"
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{listing.name}</div>
                        <div className="text-sm text-muted-foreground line-clamp-1">
                          {listing.description}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="font-semibold">
                      ${listing.price}
                    </TableCell>
                    <TableCell>
                      <div
                        className={`inline-flex items-center justify-center px-3 py-1 rounded-md text-white font-medium text-sm ${getPlatformColor(
                          listing.platform
                        )}`}
                      >
                        {String(listing.platform).toLowerCase() === "tetsy"
                          ? "Tetsy"
                          : String(listing.platform).charAt(0).toUpperCase() + String(listing.platform).slice(1)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusConfig[listing.status].variant}>
                        {statusConfig[listing.status].label}
                      </Badge>
                    </TableCell>
                    <TableCell className="capitalize">
                      {listing.category}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toast.info("View functionality coming soon")}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(listing.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </div>
    </div>
  );
}
