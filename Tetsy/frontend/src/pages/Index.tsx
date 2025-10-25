import { useState, useEffect } from "react";
import { toast } from "sonner";
import Navigation from "@/components/Navigation";
import ProductDashboard from "@/components/ProductDashboard";
import ChatInterface, { type Negotiation } from "@/components/ChatInterface";
import OfferDialog from "@/components/OfferDialog";
import { type Product } from "@/components/ProductCard";
import { api } from "@/lib/api";

const mockProducts: Product[] = [
  {
    id: "1",
    title: "Handcrafted Ceramic Vase",
    price: 45.00,
    image: "https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=400&h=400&fit=crop",
    seller: "PotteryByJane",
    description: "Beautiful handmade ceramic vase with unique glaze pattern"
  },
  {
    id: "2",
    title: "Vintage Leather Journal",
    price: 32.50,
    image: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400&h=400&fit=crop",
    seller: "LeatherCrafts",
    description: "Genuine leather journal with hand-stitched binding"
  },
  {
    id: "3",
    title: "Knitted Wool Blanket",
    price: 89.99,
    image: "https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=400&h=400&fit=crop",
    seller: "CozyKnits",
    description: "Soft merino wool blanket, perfect for cold nights"
  },
  {
    id: "4",
    title: "Hand-Painted Wooden Jewelry Box",
    price: 56.00,
    image: "https://images.unsplash.com/photo-1585933646001-c2836e3c0c54?w=400&h=400&fit=crop",
    seller: "WoodWorkArt",
    description: "Beautifully painted wooden jewelry box with velvet interior"
  },
  {
    id: "5",
    title: "Artisan Candle Set",
    price: 28.00,
    image: "https://images.unsplash.com/photo-1602874801006-c2b93a59fccf?w=400&h=400&fit=crop",
    seller: "ScentedMoments",
    description: "Set of 3 soy candles with natural essential oils"
  },
  {
    id: "6",
    title: "Macramé Wall Hanging",
    price: 42.00,
    image: "https://images.unsplash.com/photo-1600494603989-9650cf6ddd3d?w=400&h=400&fit=crop",
    seller: "BohoDecor",
    description: "Handmade macramé wall art in natural cotton"
  },
  {
    id: "7",
    title: "Copper Plant Pot",
    price: 38.50,
    image: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=400&h=400&fit=crop",
    seller: "MetalCraft",
    description: "Hammered copper planter with drainage hole"
  },
  {
    id: "8",
    title: "Handwoven Basket",
    price: 34.00,
    image: "https://images.unsplash.com/photo-1588854337221-4cf9fa96a7d1?w=400&h=400&fit=crop",
    seller: "WeaversCo",
    description: "Natural fiber basket with leather handles"
  }
];

const Index = () => {
  const [activeView, setActiveView] = useState<"shop" | "messages">("shop");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [offerDialogOpen, setOfferDialogOpen] = useState(false);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [loading, setLoading] = useState(true);

  // Load negotiations from API on mount
  useEffect(() => {
    loadNegotiations();
    
    // Poll for updates every 3 seconds
    const interval = setInterval(() => {
      loadNegotiations();
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
    const product = mockProducts.find(p => p.id === productId);
    if (!product) return;

    try {
      const { data } = await api.post("/api/negotiations", {
        product_id: product.id,
        product_title: product.title,
        product_image: product.image,
        seller_id: product.seller,
        offer_amount: offerAmount,
        message: message || `I'd like to offer $${offerAmount.toFixed(2)} for this item.`
      });

      setNegotiations(prev => [data, ...prev]);
      setOfferDialogOpen(false);
      
      toast.success(`Offer sent for $${offerAmount.toFixed(2)}`, {
        description: `Sent to ${product.seller}`
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
        <ProductDashboard products={mockProducts} onMakeOffer={handleMakeOffer} />
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
