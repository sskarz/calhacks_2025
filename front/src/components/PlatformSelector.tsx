import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

export type Platform = "etsy" | "ebay";

interface PlatformSelectorProps {
  onSelect: (platform: Platform) => void;
  selectedPlatform?: Platform;
}

const platforms = [
  {
    id: "Tetsy" as Platform,
    name: "Tetsy",
    description: "Perfect for handmade, vintage, and unique goods",
    color: "from-orange-500 to-orange-600",
  },
  {
    id: "ebay" as Platform,
    name: "eBay",
    description: "Ideal for auctions and general marketplace items",
    color: "from-blue-500 to-blue-600",
  },
];

export const PlatformSelector = ({ onSelect, selectedPlatform }: PlatformSelectorProps) => {
  const [selected, setSelected] = useState<Platform | undefined>(selectedPlatform);

  const handleSelect = (platform: Platform) => {
    setSelected(platform);
    onSelect(platform);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {platforms.map((platform) => (
          <Card
            key={platform.id}
            className={cn(
              "p-6 cursor-pointer transition-all duration-300 hover:shadow-lg",
              selected === platform.id
                ? "ring-2 ring-primary shadow-lg"
                : "hover:ring-1 hover:ring-border"
            )}
            onClick={() => handleSelect(platform.id)}
          >
            <div className="flex items-start justify-between mb-4">
              <div
                className={cn(
                  "w-16 h-16 rounded-lg bg-gradient-to-br flex items-center justify-center text-white font-bold text-2xl",
                  platform.color
                )}
              >
                {platform.name[0]}
              </div>
              {selected === platform.id && (
                <div className="w-8 h-8 rounded-full bg-success flex items-center justify-center">
                  <Check className="w-5 h-5 text-success-foreground" />
                </div>
              )}
            </div>
            <h3 className="text-xl font-semibold mb-2">{platform.name}</h3>
            <p className="text-muted-foreground text-sm">{platform.description}</p>
          </Card>
        ))}
      </div>
    </div>
  );
};
