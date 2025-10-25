import { MessageSquare, ShoppingBag } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NavigationProps {
  activeView: "shop" | "messages";
  onViewChange: (view: "shop" | "messages") => void;
}

const Navigation = ({ activeView, onViewChange }: NavigationProps) => {
  return (
    <nav className="sticky top-0 z-50 bg-card border-b border-border shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Tetsy
          </h1>
          
          <div className="flex gap-2">
            <Button
              variant={activeView === "shop" ? "default" : "ghost"}
              onClick={() => onViewChange("shop")}
              className="gap-2"
            >
              <ShoppingBag className="h-4 w-4" />
              Shop
            </Button>
            <Button
              variant={activeView === "messages" ? "default" : "ghost"}
              onClick={() => onViewChange("messages")}
              className="gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Messages
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
