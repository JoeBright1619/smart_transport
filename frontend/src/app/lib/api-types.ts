// Response envelopes
export interface ApiMeta {
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<T> {
  data: T;
  meta?: ApiMeta;
  error?: ApiError;
}

export type PaginatedResponse<T> = ApiResponse<T[]>;

// Auth (JSON field names match backend APIModel camelCase serialization)
export interface AuthUserSummary {
  id: string;
  email: string | null;
  fullName: string | null;
  role: UserRole;
  tenantId: string | null;
}

export interface AuthTenantSummary {
  id: string;
  name: string;
  isActive: boolean;
}

export interface RegisterResponse {
  tenant: AuthTenantSummary;
  user: AuthUserSummary;
  accessToken: string;
}

export interface TokenResponse {
  accessToken: string;
  user: AuthUserSummary;
}

export interface RefreshTokenResponse {
  accessToken: string;
}

// Users
export type UserRole = 'superadmin' | 'admin' | 'operator' | 'dispatcher' | 'passenger';
export type TenantUserRole = 'admin' | 'operator' | 'dispatcher' | 'passenger';

export interface UserRead {
  id: string;
  tenant_id: string | null;
  full_name: string;
  email: string;
  role: UserRole;
  phone: string | null;
  is_deleted: boolean;
  created_at: string;
}

export interface UserCreate {
  full_name: string;
  email: string;
  role: TenantUserRole;
  phone?: string;
  password: string;
}

export interface UserUpdate {
  full_name?: string;
  phone?: string;
  role?: TenantUserRole;
}

// Vehicles
export type VehicleStatus = 'active' | 'idle' | 'maintenance' | 'offline';
export type EngineStatus = 'good' | 'warning' | 'critical';

export interface VehicleLocation {
  lat: number;
  lng: number;
}

export interface VehicleRead {
  id: string;
  registrationNumber: string;
  model: string;
  capacity: number;
  status: VehicleStatus;
  speed: number | null;
  heading: number | null;
  fuel: number | null;
  engineStatus: EngineStatus;
  currentLocation: VehicleLocation | null;
  routeId: string | null;
  driverId: string | null;
  lastUpdate: string;
}

export interface VehicleCreate {
  registration_number: string;
  model: string;
  capacity: number;
  status?: VehicleStatus;
}

export interface VehicleUpdate {
  status?: VehicleStatus;
  fuel?: number;
  route_id?: string | null;
  driver_id?: string | null;
}

// Routes & Stops
export interface StopRead {
  id: string;
  name: string;
  lat: number;
  lng: number;
  order: number;
}

export interface StopCreate {
  name: string;
  lat: number;
  lng: number;
  order: number;
}

export interface RouteRead {
  id: string;
  name: string;
  number: string;
  distance: number;
  duration: number;
  color: string;
  is_active: boolean;
  created_at: string;
  stops: StopRead[];
}

export interface RouteCreate {
  name: string;
  number: string;
  distance: number;
  duration: number;
  color: string;
  stops: StopCreate[];
}

export interface RouteUpdate {
  name?: string;
  is_active?: boolean;
  color?: string;
  stops?: StopCreate[];
}

// Drivers
export type DriverStatus = 'available' | 'on-trip' | 'off-duty';

export interface DriverRead {
  id: string;
  name: string;
  licenseNumber: string;
  phone: string;
  rating: number;
  totalTrips: number;
  status: DriverStatus;
  vehicleId: string | null;
  certificationExpiry: string;
  createdAt: string;
}

export interface DriverCreate {
  name: string;
  license_number: string;
  phone: string;
  certification_expiry: string;
}

export interface DriverUpdate {
  name?: string;
  phone?: string;
  status?: DriverStatus;
  vehicle_id?: string | null;
  certification_expiry?: string;
}

// Trips
export type TripStatus = 'scheduled' | 'active' | 'completed' | 'cancelled';

export interface TripRead {
  id: string;
  vehicleId: string;
  routeId: string;
  driverId: string;
  scheduledStart: string;
  actualStart: string | null;
  scheduledEnd: string;
  actualEnd: string | null;
  status: TripStatus;
  passengers: number;
  delay: number;
  createdAt: string;
}

export interface TripCreate {
  vehicle_id: string;
  route_id: string;
  driver_id: string;
  scheduled_start: string;
  scheduled_end: string;
}

export interface TripUpdate {
  status: TripStatus;
}

// Alerts
export type AlertType =
  | 'delay'
  | 'breakdown'
  | 'maintenance'
  | 'geofence'
  | 'speeding'
  | 'info';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface AlertRead {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  vehicleId: string | null;
  driverId: string | null;
  isAcknowledged: boolean;
  createdAt: string;
}

// Maintenance
export type MaintenanceType = 'routine' | 'repair' | 'inspection';
export type MaintenanceStatus = 'scheduled' | 'in-progress' | 'completed';

export interface MaintenanceRead {
  id: string;
  vehicleId: string;
  type: MaintenanceType;
  description: string;
  scheduledDate: string;
  completedDate: string | null;
  cost: number;
  status: MaintenanceStatus;
  nextDue: string | null;
  createdAt: string;
}

export interface MaintenanceCreate {
  vehicle_id: string;
  type: MaintenanceType;
  description: string;
  scheduled_date: string;
  cost: number;
}

export interface MaintenanceUpdate {
  status?: MaintenanceStatus;
  cost?: number;
  completed_date?: string;
  next_due?: string;
}

// Analytics
export interface AnalyticsSummary {
  totalTrips: number;
  onTimePercentage: number;
  avgDelay: number;
  totalPassengers: number;
  totalRevenue: number;
  totalFuelConsumption: number;
}

export interface AnalyticsDaily {
  date: string;
  totalTrips: number;
  onTimePercentage: number;
  avgDelay: number;
  totalPassengers: number;
  fuelConsumption: number;
  revenue: number;
}

export interface AnalyticsData {
  summary: AnalyticsSummary;
  daily: AnalyticsDaily[];
}

// Arrivals
export interface ArrivalEstimate {
  vehicle_id: string;
  registration_number: string;
  route_id: string;
  route_name: string;
  distance_to_stop_km: number;
  current_speed_kmh: number;
  eta_minutes: number | null;
  estimated_arrival_time: string | null;
  status: string;
}

// Superadmin
export interface TenantRead {
  id: string;
  name: string;
  contactEmail: string;
  isActive: boolean;
  createdAt: string;
  vehicleCount: number;
  userCount: number;
}

export interface TenantDetail extends TenantRead {
  updatedAt: string;
}

export interface SuperadminAnalytics {
  totalTenants: number;
  activeTenants: number;
  totalVehicles: number;
  totalTripsToday: number;
  totalPassengersToday: number;
}

export interface ImpersonateResponse {
  accessToken: string;
}

// WebSocket
export type WsVehiclePosition = {
  vehicleId: string;
  lat: number;
  lng: number;
  speed: number;
  heading: number;
  fuel: number;
  status: VehicleStatus;
  timestamp: string;
};

export type WsMessage = {
  type: 'vehicle_positions';
  vehicles: WsVehiclePosition[];
};
