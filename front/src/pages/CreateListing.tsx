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
import { createListing, analyzeProductImage, createListingWithAgent } from "@/lib/api";

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
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleImageSelect = async (file: File) => {
    setImageFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Analyze the image with Gemini
    setIsAnalyzing(true);
    toast.loading("Analyzing product image...", { id: "image-analysis" });

    try {
      const analysis = await analyzeProductImage(file);

      // Set initial product details with analyzed data
      setProductDetails({
        name: analysis.name,
        description: analysis.description,
        price: analysis.price,
        quantity: analysis.quantity,
        brand: analysis.brand,
        category: "",
        condition: "",
      });

      toast.success("Product details extracted! Review and edit as needed.", {
        id: "image-analysis",
      });
    } catch (error) {
      console.error("Error analyzing image:", error);
      toast.error("Failed to analyze image. Please fill in details manually.", {
        id: "image-analysis",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview("");
    setProductDetails(null);
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
      toast.loading("Orchestrator agent is processing your listing...", { id: "agent-listing" });

      // Call the orchestrator agent to create the listing

      const agentResponse = await createListingWithAgent(
        {
          name: productDetails.name,
          description: productDetails.description,
          price: productDetails.price,
          quantity: productDetails.quantity,
          brand: productDetails.brand,
        },
        selectedPlatform,
        imageFile
      );

      console.log("Agent response:", agentResponse);

      toast.success(
        `Listing created successfully via ${selectedPlatform} agent! ${agentResponse.message}`,
        { id: "agent-listing" }
      );

      navigate("/");
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to create listing via agent";
      toast.error(errorMessage, { id: "agent-listing" });
      console.error("Agent error:", error);
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
                  disabled={!imageFile || isAnalyzing}
                  size="lg"
                >
                  {isAnalyzing ? "Analyzing..." : "Next Step"}
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
                  {productDetails?.name ? "Review and edit the auto-filled details" : "Tell us about your product"}
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
