import { useCallback, useState } from "react";
import { Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  preview?: string;
  onRemove?: () => void;
}

export const ImageUpload = ({ onImageSelect, preview, onRemove }: ImageUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        onImageSelect(file);
      }
    },
    [onImageSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelect(file);
    }
  };

  if (preview) {
    return (
      <div className="relative w-full aspect-square rounded-lg overflow-hidden border-2 border-border">
        <img src={preview} alt="Preview" className="w-full h-full object-cover" />
        {onRemove && (
          <Button
            variant="destructive"
            size="icon"
            className="absolute top-2 right-2"
            onClick={onRemove}
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      className={cn(
        "w-full aspect-square rounded-lg border-2 border-dashed transition-colors duration-300",
        "flex flex-col items-center justify-center cursor-pointer",
        isDragging
          ? "border-primary bg-primary/5"
          : "border-border hover:border-primary hover:bg-muted/50"
      )}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="hidden"
        id="image-upload"
      />
      <label htmlFor="image-upload" className="flex flex-col items-center cursor-pointer p-8">
        <Upload className="w-16 h-16 text-muted-foreground mb-4" />
        <p className="text-lg font-medium text-foreground mb-2">
          Drop your image here
        </p>
        <p className="text-sm text-muted-foreground">or click to browse</p>
      </label>
    </div>
  );
};
