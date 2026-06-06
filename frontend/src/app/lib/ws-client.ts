import { getStoredToken, clearStoredToken } from './api-client';
import type { WsMessage } from './api-types';

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000';

export class VehicleTrackingSocket {
  private socket: WebSocket | null = null;
  private onMessage: (msg: WsMessage) => void;
  private onError?: (err: Event) => void;
  private onClose?: () => void;

  constructor(
    onMessage: (msg: WsMessage) => void,
    onError?: (err: Event) => void,
    onClose?: () => void,
  ) {
    this.onMessage = onMessage;
    this.onError = onError;
    this.onClose = onClose;
  }

  connect(): void {
    if (this.socket) return;

    const token = getStoredToken();
    const url = `${WS_URL}/ws/tracking?token=${encodeURIComponent(token ?? '')}`;

    this.socket = new WebSocket(url);

    this.socket.onmessage = (event) => {
      try {
        const rawData = JSON.parse(event.data);
        if (rawData.type === 'vehicle_update') {
          const mappedMessage: WsMessage = {
            type: 'vehicle_positions',
            vehicles: rawData.data.map((v: any) => ({
              vehicleId: v.vehicleId,
              lat: v.lat,
              lng: v.lng,
              speed: v.speed,
              heading: v.heading,
              fuel: v.fuel,
              status: 'active',
              timestamp: v.timestamp,
              engineStatus: v.engineStatus,
              nextStopName: v.nextStopName ?? '',
              progressPct: v.progressPct ?? 0,
              atStop: v.atStop ?? '',
              currentOccupancy: v.currentOccupancy,
              seatingCapacity: v.seatingCapacity,
              remainingSeats: v.remainingSeats,
            })),
          };
          this.onMessage(mappedMessage);
        } else if (rawData.type === 'vehicle_positions') {
          this.onMessage(rawData);
        } else if (rawData.type === 'vehicle_occupancy_updated') {
          this.onMessage(rawData as WsMessage);
        }
      } catch (err) {
        console.error('Error parsing WS message', err);
      }
    };

    this.socket.onerror = (event) => {
      if (this.onError) {
        this.onError(event);
      }
    };

    this.socket.onclose = (event) => {
      this.socket = null;
      if (event.code === 4001) {
        clearStoredToken();
        if (window.location.pathname !== '/login') {
          window.location.assign('/login');
        }
        return;
      }
      if (this.onClose) {
        this.onClose();
      }
    };
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  get isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}
