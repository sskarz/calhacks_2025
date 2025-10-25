import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { type Product } from "./ProductCard";
import { DollarSign } from "lucide-react";

interface OfferDialogProps {
  product: Product | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmitOffer: (productId: string, offerAmount: number, message: string) => void;
}

const OfferDialog = ({ product, open, onOpenChange, onSubmitOffer }: OfferDialogProps) => {
  const [offerAmount, setOfferAmount] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = () => {
    if (!product || !offerAmount) return;
    
    const amount = parseFloat(offerAmount);
    if (isNaN(amount) || amount <= 0) return;
    
    onSubmitOffer(product.id, amount, message);
    setOfferAmount("");
    setMessage("");
    onOpenChange(false);
  };

  if (!product) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Make an Offer</DialogTitle>
          <DialogDescription>
            Send an offer to {product.seller} for this item
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid gap-4 py-4">
          <div className="flex items-start gap-4">
            <img
              src={product.image}
              alt={product.title}
              className="w-24 h-24 object-cover rounded-lg border border-border"
            />
            <div className="flex-1">
              <h4 className="font-semibold text-foreground">{product.title}</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Listed at ${product.price.toFixed(2)}
              </p>
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="offer">Your Offer Amount</Label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="offer"
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={offerAmount}
                onChange={(e) => setOfferAmount(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="message">Message (Optional)</Label>
            <Textarea
              id="message"
              placeholder="Add a message to the seller..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="resize-none"
              rows={3}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!offerAmount || parseFloat(offerAmount) <= 0}
            className="bg-accent hover:bg-accent/90"
          >
            Send Offer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default OfferDialog;
