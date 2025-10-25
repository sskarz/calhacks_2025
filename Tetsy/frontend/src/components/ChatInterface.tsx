import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, DollarSign, Check, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export interface Negotiation {
  id: string;
  productId: string;
  productTitle: string;
  productImage: string;
  seller: string;
  messages: Message[];
  status: "pending" | "accepted" | "rejected";
  lastOfferAmount?: number;
}

export interface Message {
  id: string;
  sender: "buyer" | "seller";
  content: string;
  timestamp: Date;
  type: "message" | "offer";
  offerAmount?: number;
}

interface ChatInterfaceProps {
  negotiations: Negotiation[];
  onSendMessage: (negotiationId: string, message: string) => void;
  onRespondToOffer: (negotiationId: string, accept: boolean) => void;
}

const ChatInterface = ({ negotiations, onSendMessage, onRespondToOffer }: ChatInterfaceProps) => {
  const [selectedNegotiation, setSelectedNegotiation] = useState<Negotiation | null>(
    negotiations[0] || null
  );
  const [messageInput, setMessageInput] = useState("");

  const handleSendMessage = () => {
    if (!selectedNegotiation || !messageInput.trim()) return;
    onSendMessage(selectedNegotiation.id, messageInput);
    setMessageInput("");
  };

  const getStatusColor = (status: Negotiation["status"]) => {
    switch (status) {
      case "accepted":
        return "bg-accent/10 text-accent";
      case "rejected":
        return "bg-destructive/10 text-destructive";
      default:
        return "bg-primary/10 text-primary";
    }
  };

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
                    onClick={() => setSelectedNegotiation(negotiation)}
                    className={`w-full p-4 text-left transition-colors border-b border-border hover:bg-muted/50 ${
                      selectedNegotiation?.id === negotiation.id ? "bg-muted" : ""
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
                  <div className="space-y-4">
                    {selectedNegotiation.messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.sender === "buyer" ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-[70%] rounded-lg p-3 ${
                            message.sender === "buyer"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-foreground"
                          }`}
                        >
                          {message.type === "offer" && message.offerAmount && (
                            <div className="flex items-center gap-2 font-semibold mb-1">
                              <DollarSign className="h-4 w-4" />
                              Offer: ${message.offerAmount.toFixed(2)}
                            </div>
                          )}
                          <p className="text-sm">{message.content}</p>
                          <p className="text-xs opacity-70 mt-1">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>

                {selectedNegotiation.status === "pending" && (
                  <div className="p-4 border-t border-border">
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
