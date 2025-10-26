import { useState, useEffect } from "react";
import { toast } from "sonner";
import Navigation from "@/components/Navigation";
import ProductDashboard from "@/components/ProductDashboard";
import ChatInterface, { type Negotiation } from "@/components/ChatInterface";
import OfferDialog from "@/components/OfferDialog";
import { type Product } from "@/components/ProductCard";
import { api } from "@/lib/api";


const Index = () => {
  const [activeView, setActiveView] = useState<"shop" | "messages">("shop");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [offerDialogOpen, setOfferDialogOpen] = useState(false);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [loading, setLoading] = useState(true);
  const [listings, setListings] = useState<Product[]>([]);

  // Load negotiations from API on mount
  useEffect(() => {
    loadNegotiations();
    loadListings();

    
    // Poll for updates every 3 seconds
    const interval = setInterval(() => {
      loadNegotiations();
      loadListings();
    }, 3000);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  const loadNegotiations = async () => {
    try {
      const { data } = await api.get("/api/negotiations");
      setNegotiations(data);
    } catch (error) {
      console.error("Failed to load negotiations:", error);
      if (loading) {
        toast.error("Failed to load negotiations");
      }
    } finally {
      setLoading(false);
    }
  };

  const loadListings = async () => {
    try {
      const { data } = await api.get("/api/listing");
      setListings(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load listings:", error);
      toast.error("Failed to load listings");
    }
  };

  const loadSingleNegotiation = async (negotiationId: string) => {
    try {
      const { data } = await api.get(`/api/negotiations/${negotiationId}`);
      setNegotiations(prev => 
        prev.map(n => n.id === negotiationId ? data : n)
      );
      return data;
    } catch (error) {
      console.error("Failed to load negotiation:", error);
      throw error;
    }
  };

  const handleMakeOffer = (product: Product) => {
    setSelectedProduct(product);
    setOfferDialogOpen(true);
  };

  const handleSubmitOffer = async (productId: string, offerAmount: number, message: string) => {
    const product = listings.find(p => p.id === productId);
    if (!product) return;

    try {
      const { data } = await api.post("/api/negotiations", {
        product_id: product.id,
        product_title: product.name,
        product_image: product.image,
        seller_id: product.seller_id,
        offer_amount: offerAmount,
        message: message || `I'd like to offer $${offerAmount.toFixed(2)} for this item.`
      });

      setNegotiations(prev => [data, ...prev]);
      setOfferDialogOpen(false);
      
      toast.success(`Offer sent for $${offerAmount.toFixed(2)}`, {
        description: `Sent to ${product.seller_id}`
      });

      setActiveView("messages");
    } catch (error) {
      console.error("Failed to submit offer:", error);
      toast.error("Failed to send offer", {
        description: "Please try again."
      });
    }
  };

  const handleSendMessage = async (negotiationId: string, messageContent: string, offerAmount?: number) => {
    try {
      const type = offerAmount ? "offer" : "message";
      
      await api.post(`/api/negotiations/${negotiationId}/messages`, {
        negotiationId,
        content: messageContent,
        type,
        offerAmount: offerAmount || undefined
      });

      await loadSingleNegotiation(negotiationId);

      if (offerAmount) {
        toast.success(`Counter offer sent for $${offerAmount.toFixed(2)}`);
      } else {
        toast.success("Message sent");
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message", {
        description: "Please try again."
      });
    }
  };

  const handleRespondToOffer = async (negotiationId: string, accept: boolean) => {
    try {
      if (accept) {
        await api.post(`/api/negotiations/${negotiationId}/accept`);
      }

      await loadSingleNegotiation(negotiationId);

      if (accept) {
        toast.success("Offer accepted!", {
          description: "Congratulations on your purchase"
        });
      } else {
        toast.info("Offer declined");
      }
    } catch (error) {
      console.error("Failed to respond to offer:", error);
      toast.error("Failed to respond to offer", {
        description: "Please try again."
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation activeView={activeView} onViewChange={setActiveView} />
      
      {activeView === "shop" ? (
        <ProductDashboard products={listings} onMakeOffer={handleMakeOffer} />
      ) : (
        <ChatInterface
          negotiations={negotiations}
          onSendMessage={handleSendMessage}
          onRespondToOffer={handleRespondToOffer}
        />
      )}

      <OfferDialog
        product={selectedProduct}
        open={offerDialogOpen}
        onOpenChange={setOfferDialogOpen}
        onSubmitOffer={handleSubmitOffer}
      />
    </div>
  );
};

export default Index;
