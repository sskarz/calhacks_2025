import axios from 'axios';
import type { Listing } from '@/types/listing';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// WebSocket connection manager
export const wsManager = {
  ws: null as WebSocket | null,

  connect(onMessage: (data: any) => void, onError?: (error: Error) => void) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${protocol}//localhost:8000/api/stream`);

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        onError?.(new Error('Failed to parse WebSocket data'));
      }
    };

    this.ws.onerror = () => {
      onError?.(new Error('WebSocket error occurred'));
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      setTimeout(() => this.connect(onMessage, onError), 3000);
    };
  },

  disconnect() {
    this.ws?.close();
  }
};

// Listing API endpoints
export async function createListing(formData: FormData): Promise<Listing> {
  const response = await api.post('/add_item', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export interface ProductAnalysis {
  name: string;
  description: string;
  price: string;
  quantity: string;
  brand: string;
}

export async function analyzeProductImage(imageFile: File): Promise<ProductAnalysis> {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await api.post('/analyze-product-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export interface AgentListingResponse {
  message: string;
  status: string;
  agent_response: any;
}

export async function createListingWithAgent(
  productData: {
    name: string;
    description: string;
    price: string;
    quantity: string;
    brand: string;
  },
  platform: string,
  imageFile: File
): Promise<AgentListingResponse> {
  const formData = new FormData();
  formData.append('name', productData.name);
  formData.append('description', productData.description);
  formData.append('price', productData.price);
  formData.append('quantity', productData.quantity);
  formData.append('brand', productData.brand);
  formData.append('platform', platform);
  formData.append('image', imageFile); // Placeholder empty image

  const response = await api.post('/create-listing-with-agent', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

