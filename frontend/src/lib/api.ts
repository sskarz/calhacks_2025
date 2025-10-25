import axios from 'axios';

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

