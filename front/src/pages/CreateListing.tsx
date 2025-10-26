import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { StepIndicator } from "../components/StepIndicator";
import { ImageUpload } from "@/components/ImageUpload";
import { ProductDetailsForm, type ProductDetails } from "@/components/ProductDetailsForm";
import { PlatformSelector, type Platform } from "@/components/PlatformSelector";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import type { Listing } from "@/types/listing";
import { createListing } from "@/lib/api"; // Adjust the import based on your project structure

const steps = [
  { number: 1, title: "Upload Image" },
  { number: 2, title: "Product Details" },
  { number: 3, title: "Select Platform" },
];

export default function CreateListing() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [productDetails, setProductDetails] = useState<ProductDetails | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | undefined>();

  const handleImageSelect = (file: File) => {
    setImageFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview("");
  };

  const handleProductDetailsSubmit = (data: ProductDetails) => {
    setProductDetails(data);
    setCurrentStep(3);
  };

  const handleFinish = async () => {
    if (!imageFile || !productDetails || !selectedPlatform) {
      toast.error("Please complete all steps");
      return;
    }

    try {
      const formData = new FormData();
      formData.append('title', productDetails.name);
      formData.append('description', productDetails.description);
      formData.append('platform', selectedPlatform);
      formData.append('price', productDetails.price.toString());
      formData.append('status', 'draft');
      formData.append('quantity', '1');
      formData.append('image', imageFile);

      await createListing(formData);
      
      toast.success("Listing created successfully!");
      navigate("/");
    } catch (error) {
      toast.error("Failed to create listing");
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container max-w-5xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate("/")}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <h1 className="text-4xl font-bold">Create New Listing</h1>
          <p className="text-muted-foreground mt-2">
            Follow the steps below to create your listing
          </p>
        </div>

        <StepIndicator steps={steps} currentStep={currentStep} />

        <Card className="p-8 mt-8">
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-2">Upload Product Image</h2>
                <p className="text-muted-foreground">
                  Add a clear photo of the item you want to sell
                </p>
              </div>
              <div className="max-w-md mx-auto">
                <ImageUpload
                  onImageSelect={handleImageSelect}
                  preview={imagePreview}
                  onRemove={handleRemoveImage}
                />
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={() => setCurrentStep(2)}
                  disabled={!imageFile}
                  size="lg"
                >
                  Next Step
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-2">Product Details</h2>
                <p className="text-muted-foreground">
                  Tell us about your product
                </p>
              </div>
              <div className="max-w-2xl mx-auto">
                <ProductDetailsForm
                  onSubmit={handleProductDetailsSubmit}
                  initialData={productDetails || undefined}
                />
              </div>
              <div className="flex justify-start">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(1)}
                  size="lg"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Previous
                </Button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-semibold mb-2">Choose Platform</h2>
                <p className="text-muted-foreground">
                  Select where you want to list this item
                </p>
              </div>
              <PlatformSelector
                onSelect={setSelectedPlatform}
                selectedPlatform={selectedPlatform}
              />
              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(2)}
                  size="lg"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Previous
                </Button>
                <Button
                  onClick={handleFinish}
                  disabled={!selectedPlatform}
                  size="lg"
                  className="bg-accent hover:bg-accent/90"
                >
                  Create Listing
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
