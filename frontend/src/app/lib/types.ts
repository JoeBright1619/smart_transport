// Type definitions for the transport system

export type UserRole = 'superadmin' | 'admin' | 'operator' | 'dispatcher' | 'passenger';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  phone?: string;
  company?: string;
}

export type VehicleStatus = 'active' | 'idle' | 'maintenance' | 'offline';

export interface Vehicle {
  id: string;
  registrationNumber: string;
  model: string;
  capacity: number;
  status: VehicleStatus;
  currentLocation: {
    lat: number;
    lng: number;
  };
  speed: number;
  heading: number;
  routeId: string | null;
  driverId: string | null;
  lastUpdate: string;
  fuel: number;
  engineStatus: 'good' | 'warning' | 'critical';
}

export interface Route {
  id: string;
  name: string;
  number: string;
  stops: Stop[];
  distance: number;
  duration: number;
  active: boolean;
  color: string;
}

export interface Stop {
  id: string;
  name: string;
  location: {
    lat: number;
    lng: number;
  };
  order: number;
}

export interface Trip {
  id: string;
  vehicleId: string;
  routeId: string;
  driverId: string;
  scheduledStart: string;
  actualStart: string | null;
  scheduledEnd: string;
  actualEnd: string | null;
  status: 'scheduled' | 'active' | 'completed' | 'cancelled';
  passengers: number;
  delay: number;
}

export interface Driver {
  id: string;
  name: string;
  licenseNumber: string;
  phone: string;
  rating: number;
  totalTrips: number;
  status: 'available' | 'on-trip' | 'off-duty';
  vehicleId: string | null;
  certificationExpiry: string;
}

export interface MaintenanceRecord {
  id: string;
  vehicleId: string;
  type: 'routine' | 'repair' | 'inspection';
  description: string;
  scheduledDate: string;
  completedDate: string | null;
  cost: number;
  status: 'scheduled' | 'in-progress' | 'completed';
  nextDue: string | null;
}

export interface Alert {
  id: string;
  type: 'delay' | 'breakdown' | 'maintenance' | 'geofence' | 'speeding' | 'info';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  vehicleId?: string;
  driverId?: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface Analytics {
  date: string;
  totalTrips: number;
  onTimePercentage: number;
  avgDelay: number;
  totalPassengers: number;
  fuelConsumption: number;
  revenue: number;
}
