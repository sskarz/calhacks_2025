import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DollarSign } from "lucide-react";

export interface Product {
  id: string;
  title: string;
  price: number;
  image: string;
  seller: string;
  description: string;
}

interface ProductCardProps {
  product: Product;
  onMakeOffer: (product: Product) => void;
}

const ProductCard = ({ product, onMakeOffer }: ProductCardProps) => {
  return (
    <Card className="group overflow-hidden transition-all duration-300 hover:shadow-[var(--shadow-hover)] border-border">
      <div className="aspect-square overflow-hidden bg-muted">
        <img
          src={product.image}
          alt={product.title}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold text-foreground line-clamp-1 mb-1">
          {product.title}
        </h3>
        <p className="text-sm text-muted-foreground mb-2">by {product.seller}</p>
        <div className="flex items-center gap-1 text-lg font-bold text-primary">
          <DollarSign className="h-5 w-5" />
          {product.price.toFixed(2)}
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <Button
          onClick={() => onMakeOffer(product)}
          className="w-full bg-accent hover:bg-accent/90"
        >
          Make an Offer
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ProductCard;
