import type { VehicleRead, VehicleStatus } from '../../../lib/api-types';

export const vehicleStatuses: VehicleStatus[] = ['active', 'idle', 'maintenance', 'offline'];
export const unassignedValue = 'unassigned';

export type FleetStats = {
  totalVehicles: number;
  activeVehicles: number;
  idleVehicles: number;
  maintenanceVehicles: number;
  avgFuel: number;
  totalCapacity: number;
};

export function getFleetStats(vehicles: VehicleRead[]): FleetStats {
  const totalVehicles = vehicles.length;
  const totalFuel = vehicles.reduce((sum, vehicle) => sum + (vehicle.fuel ?? 0), 0);

  return {
    totalVehicles,
    activeVehicles: vehicles.filter((vehicle) => vehicle.status === 'active').length,
    idleVehicles: vehicles.filter((vehicle) => vehicle.status === 'idle').length,
    maintenanceVehicles: vehicles.filter((vehicle) => vehicle.status === 'maintenance').length,
    avgFuel: totalVehicles > 0 ? Math.round(totalFuel / totalVehicles) : 0,
    totalCapacity: vehicles.reduce((sum, vehicle) => sum + vehicle.capacity, 0),
  };
}

export function fuelBarClass(fuel: number | null): string {
  const value = fuel ?? 0;
  if (value > 50) return 'bg-green-500';
  if (value > 25) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function formatLocation(vehicle: VehicleRead): string {
  if (!vehicle.current_location) return '-';
  const { lat, lng } = vehicle.current_location;
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
}

export function formatRelativeTime(value: string): string {
  const timestamp = new Date(value).getTime();
  if (Number.isNaN(timestamp)) return '-';

  const seconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
  if (seconds < 60) return `${seconds}s ago`;

  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  return `${Math.round(hours / 24)}d ago`;
}

export function getUtilization(status: VehicleStatus): number {
  if (status === 'active') return 100;
  if (status === 'idle') return 25;
  return 0;
}
