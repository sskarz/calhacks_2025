import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, DollarSign } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { toast } from "sonner";

export interface Negotiation {
  id: string;
  productId: string;
  productTitle: string;
  productImage: string;
  seller: string;
  messages: Message[];
  status: "pending" | "accepted" | "rejected" | "counter";
  lastOfferAmount?: number;
}

export interface Message {
  id: string;
  sender_id: string;
  sender_type: "buyer" | "seller";
  content: string;
  timestamp: string;
  type: "message" | "offer" | "counter_offer";
  offer_amount?: number;
}

interface ChatInterfaceProps {
  negotiations: Negotiation[];
  onSendMessage: (negotiationId: string, message: string, offerAmount?: number) => void;
  onRespondToOffer: (negotiationId: string, accept: boolean) => void;
}

const ChatInterface = ({ negotiations, onSendMessage, onRespondToOffer }: ChatInterfaceProps) => {
  const [selectedNegotiationId, setSelectedNegotiationId] = useState<string | null>(
    negotiations.length > 0 ? negotiations[0].id : null
  );
  const [selectedNegotiation, setSelectedNegotiation] = useState<Negotiation | null>(null);
  const [messageInput, setMessageInput] = useState("");
  const [offerAmount, setOfferAmount] = useState("");
  const [isCounterOffer, setIsCounterOffer] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // Load full negotiation details when selection changes
  useEffect(() => {
    if (!selectedNegotiationId) return;

    const loadNegotiationDetails = async () => {
      try {
        setLoadingMessages(true);
        const { data } = await api.get(`/api/negotiations/${selectedNegotiationId}`);
        setSelectedNegotiation(data);
      } catch (error) {
        console.error("Failed to load negotiation details:", error);
        toast.error("Failed to load messages");
      } finally {
        setLoadingMessages(false);
      }
    };

    loadNegotiationDetails();
  }, [selectedNegotiationId]);

  const handleSelectNegotiation = (negotiation: Negotiation) => {
    setSelectedNegotiationId(negotiation.id);
  };

  const handleSendMessage = () => {
    if (!selectedNegotiation || !messageInput.trim()) return;
    
    const offer = isCounterOffer && offerAmount ? parseFloat(offerAmount) : undefined;
    onSendMessage(selectedNegotiation.id, messageInput, offer);
    
    setMessageInput("");
    setOfferAmount("");
    setIsCounterOffer(false);
  };

  const getStatusColor = (status: Negotiation["status"]) => {
    switch (status) {
      case "accepted":
        return "bg-accent/10 text-accent";
      case "rejected":
        return "bg-destructive/10 text-destructive";
      case "counter":
        return "bg-primary/10 text-primary";
      default:
        return "bg-primary/10 text-primary";
    }
  };

  const messages = selectedNegotiation?.messages || [];
  const hasCounterOffer = messages.some(m => m.type === "counter_offer" && m.sender_type === "seller");
  const canRespond = selectedNegotiation
    ? (selectedNegotiation.status === "pending" || selectedNegotiation.status === "counter")
    : false;

  return (
    <div className="container mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-foreground mb-6">Negotiations</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Negotiations List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Active Negotiations</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px]">
              {negotiations.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">
                  No active negotiations
                </div>
              ) : (
                negotiations.map((negotiation) => (
                  <button
                    key={negotiation.id}
                    onClick={() => handleSelectNegotiation(negotiation)}
                    className={`w-full p-4 text-left transition-colors border-b border-border hover:bg-muted/50 ${
                      selectedNegotiationId === negotiation.id ? "bg-muted" : ""
                    }`}
                  >
                    <div className="flex gap-3">
                      <img
                        src={negotiation.productImage}
                        alt={negotiation.productTitle}
                        className="w-12 h-12 object-cover rounded"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm truncate">
                          {negotiation.productTitle}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {negotiation.seller}
                        </p>
                        {negotiation.lastOfferAmount && (
                          <p className="text-xs font-medium text-primary mt-1">
                            ${negotiation.lastOfferAmount.toFixed(2)} offered
                          </p>
                        )}
                      </div>
                      <Badge className={getStatusColor(negotiation.status)}>
                        {negotiation.status}
                      </Badge>
                    </div>
                  </button>
                ))
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Chat Area */}
        <Card className="lg:col-span-2">
          {selectedNegotiation ? (
            <>
              <CardHeader className="border-b border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedNegotiation.productTitle}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      Negotiating with {selectedNegotiation.seller}
                    </p>
                  </div>
                  <Badge className={getStatusColor(selectedNegotiation.status)}>
                    {selectedNegotiation.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[450px] p-4">
                  {loadingMessages ? (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-muted-foreground">Loading messages...</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {messages.length === 0 ? (
                        <p className="text-center text-muted-foreground">No messages yet</p>
                      ) : (
                        messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex ${
                              message.sender_type === "buyer" ? "justify-end" : "justify-start"
                            }`}
                          >
                            <div
                              className={`max-w-[70%] rounded-lg p-3 ${
                                message.sender_type === "buyer"
                                  ? "bg-primary text-primary-foreground"
                                  : "bg-muted text-foreground"
                              }`}
                            >
                              {(message.type === "offer" || message.type === "counter_offer") && message.offer_amount && (
                                <div className="flex items-center gap-2 font-semibold mb-1">
                                  <DollarSign className="h-4 w-4" />
                                  {message.type === "counter_offer" ? "Counter Offer" : "Offer"}: ${message.offer_amount.toFixed(2)}
                                </div>
                              )}
                              <p className="text-sm">{message.content}</p>
                              <p className="text-xs opacity-70 mt-1">
                                {new Date(message.timestamp).toLocaleTimeString()}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </ScrollArea>

                {canRespond && (
                  <div className="p-4 border-t border-border space-y-3">
                    {hasCounterOffer && (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onRespondToOffer(selectedNegotiation.id, true)}
                          className="flex-1"
                        >
                          Accept Counter Offer
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setIsCounterOffer(!isCounterOffer)}
                          className="flex-1"
                        >
                          {isCounterOffer ? "Cancel Counter" : "Make Counter Offer"}
                        </Button>
                      </div>
                    )}
                    
                    {isCounterOffer && (
                      <div className="flex gap-2">
                        <Input
                          type="number"
                          placeholder="Counter offer amount..."
                          value={offerAmount}
                          onChange={(e) => setOfferAmount(e.target.value)}
                          step="0.01"
                          min="0"
                        />
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <Input
                        placeholder="Type a message..."
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                      />
                      <Button onClick={handleSendMessage} size="icon">
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </>
          ) : (
            <CardContent className="flex items-center justify-center h-[600px]">
              <p className="text-muted-foreground">
                Select a negotiation to view messages
              </p>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
};

export default ChatInterface;
