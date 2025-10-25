import { useState } from "react";
import Navigation from "@/components/Navigation";
import ProductDashboard from "@/components/ProductDashboard";
import ChatInterface, { type Negotiation, type Message } from "@/components/ChatInterface";
import OfferDialog from "@/components/OfferDialog";
import { type Product } from "@/components/ProductCard";
import { useToast } from "@/hooks/use-toast";

// Mock data - ready to be replaced with API endpoints
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
  const { toast } = useToast();
  const [activeView, setActiveView] = useState<"shop" | "messages">("shop");
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [offerDialogOpen, setOfferDialogOpen] = useState(false);
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);

  const handleMakeOffer = (product: Product) => {
    setSelectedProduct(product);
    setOfferDialogOpen(true);
  };

  const handleSubmitOffer = (productId: string, offerAmount: number, message: string) => {
    const product = mockProducts.find(p => p.id === productId);
    if (!product) return;

    // Create new negotiation - ready to be replaced with POST /api/negotiations
    const newNegotiation: Negotiation = {
      id: `neg-${Date.now()}`,
      productId: product.id,
      productTitle: product.title,
      productImage: product.image,
      seller: product.seller,
      status: "pending",
      lastOfferAmount: offerAmount,
      messages: [
        {
          id: `msg-${Date.now()}`,
          sender: "buyer",
          content: message || `I'd like to offer $${offerAmount.toFixed(2)} for this item.`,
          timestamp: new Date(),
          type: "offer",
          offerAmount: offerAmount
        }
      ]
    };

    setNegotiations(prev => [newNegotiation, ...prev]);
    
    toast({
      title: "Offer Sent!",
      description: `Your offer of $${offerAmount.toFixed(2)} has been sent to ${product.seller}`,
    });

    setActiveView("messages");
  };

  const handleSendMessage = (negotiationId: string, messageContent: string) => {
    // Send message - ready to be replaced with POST /api/negotiations/:id/messages
    setNegotiations(prev => prev.map(neg => {
      if (neg.id === negotiationId) {
        return {
          ...neg,
          messages: [
            ...neg.messages,
            {
              id: `msg-${Date.now()}`,
              sender: "buyer",
              content: messageContent,
              timestamp: new Date(),
              type: "message"
            }
          ]
        };
      }
      return neg;
    }));

    toast({
      title: "Message Sent",
      description: "Your message has been delivered",
    });
  };

  const handleRespondToOffer = (negotiationId: string, accept: boolean) => {
    // Respond to offer - ready to be replaced with PUT /api/negotiations/:id
    setNegotiations(prev => prev.map(neg => {
      if (neg.id === negotiationId) {
        return {
          ...neg,
          status: accept ? "accepted" : "rejected"
        };
      }
      return neg;
    }));

    toast({
      title: accept ? "Offer Accepted" : "Offer Rejected",
      description: accept ? "The seller has accepted your offer!" : "The seller has declined your offer",
    });
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
