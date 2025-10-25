import ProductCard, { type Product } from "./ProductCard";

interface ProductDashboardProps {
  products: Product[];
  onMakeOffer: (product: Product) => void;
}

const ProductDashboard = ({ products, onMakeOffer }: ProductDashboardProps) => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground mb-2">
          Discover Unique Items
        </h2>
        <p className="text-muted-foreground">
          Browse handcrafted goods and make offers directly to sellers
        </p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {products.map((product) => (
          <ProductCard
            key={product.id}
            product={product}
            onMakeOffer={onMakeOffer}
          />
        ))}
      </div>
    </div>
  );
};

export default ProductDashboard;
