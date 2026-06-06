import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import type { VehicleRead } from '../../../lib/api-types';

export type TrackedVehicle = VehicleRead & {
  nextStopName?: string;
  progressPct?: number;
  atStop?: string;
};

export const STATUS_COLOR: Record<string, string> = {
  active: '#10B981',
  idle: '#F59E0B',
  maintenance: '#EF4444',
  offline: '#6B7280',
};

export function occupancyColor(ratio: number): string {
  if (ratio >= 0.9) return '#EF4444';
  if (ratio >= 0.7) return '#F59E0B';
  return '#10B981';
}

export function createVehicleIcon(status: string, heading: number, isSelected: boolean, occupancyRatio = 0) {
  let color = STATUS_COLOR[status] ?? '#6B7280';
  if (status === 'active' && occupancyRatio >= 0.8) color = occupancyColor(occupancyRatio);
  const svg = isSelected
    ? `<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
        <g transform="rotate(${heading},22,22)">
          <circle cx="22" cy="22" r="21" fill="none" stroke="#3B82F6" stroke-width="3"/>
          <circle cx="22" cy="22" r="15" fill="${color}" stroke="white" stroke-width="2"/>
          <polygon points="22,9 27,25 22,21 17,25" fill="white" opacity="0.9"/>
        </g>
      </svg>`
    : `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <g transform="rotate(${heading},16,16)">
          <circle cx="16" cy="16" r="12" fill="${color}" stroke="white" stroke-width="2"/>
          <polygon points="16,6 20,20 16,17 12,20" fill="white" opacity="0.9"/>
        </g>
      </svg>`;
  const size = isSelected ? 44 : 32;
  const anchor = size / 2;
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(svg)}`,
    iconSize: [size, size],
    iconAnchor: [anchor, anchor],
    popupAnchor: [0, -anchor],
  });
}

export function MapController({ selectedVehicle }: { selectedVehicle: TrackedVehicle | null }) {
  const map = useMap();
  useEffect(() => {
    if (selectedVehicle?.currentLocation) {
      map.panTo(
        [selectedVehicle.currentLocation.lat, selectedVehicle.currentLocation.lng],
        { animate: true },
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVehicle?.id, map]);
  return null;
}
