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
  tenantName: string | null;
  tenantEmail: string | null;
  tenantAddress: string | null;
  tenantPhone: string | null;
  tenantLogoPath: string | null;
}

export interface AuthTenantSummary {
  id: string;
  name: string;
  contactEmail: string;
  address: string | null;
  phone: string | null;
  logoPath: string | null;
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
  tenantId: string | null;
  fullName: string;
  email: string;
  role: UserRole;
  phone: string | null;
  status: string;
  isDeleted: boolean;
  createdAt: string;
}

export interface UserCreate {
  fullName: string;
  email: string;
  role: TenantUserRole;
  phone?: string;
  password?: string;
}

export interface AcceptInviteRequest {
  token: string;
  newPassword: string;
}

export interface UserUpdate {
  fullName?: string;
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
  seatingCapacity: number;
  currentOccupancy: number;
  remainingSeats: number;
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
  registrationNumber: string;
  model: string;
  capacity: number;
  seatingCapacity?: number;
  status?: VehicleStatus;
}

export interface VehicleUpdate {
  status?: VehicleStatus;
  fuel?: number;
  seatingCapacity?: number;
  routeId?: string | null;
  driverId?: string | null;
}

// Routes & Stops
export interface StopRead {
  id: string;
  name: string;
  lat: number;
  lng: number;
  order: number;
}

export interface GlobalStopRead {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface StopCreate {
  stopId: string;
  order: number;
}

export interface GlobalStopCreate {
  name: string;
  lat: number;
  lng: number;
}

export interface RouteRead {
  id: string;
  name: string;
  number: string;
  distance: number;
  duration: number;
  color: string;
  isActive: boolean;
  createdAt: string;
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
  number?: string;
  distance?: number;
  duration?: number;
  isActive?: boolean;
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
  licenseNumber: string;
  phone: string;
  certificationExpiry: string;
}

export interface DriverUpdate {
  name?: string;
  phone?: string;
  status?: DriverStatus;
  vehicleId?: string | null;
  certificationExpiry?: string;
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
  vehicleId: string;
  routeId: string;
  driverId: string;
  scheduledStart: string;
  scheduledEnd: string;
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

// Audit
export interface AuditLogRead {
  id: string;
  userId: string;
  tenantId: string | null;
  resourceType: string;
  resourceId: string;
  action: string;
  metadata: Record<string, unknown> | null;
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
  vehicleId: string;
  type: MaintenanceType;
  description: string;
  scheduledDate: string;
  cost: number;
  nextDue?: string;
}

export interface MaintenanceUpdate {
  status?: MaintenanceStatus;
  cost?: number;
  completedDate?: string;
  nextDue?: string;
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

export interface RouteReportData {
  routeId: string;
  routeName: string;
  onTimeRate: number;
  avgTripDurationMinutes: number;
  totalPassengers: number;
  utilisationPercentage: number;
}

export interface DailyReportData {
  date: string;
  totalTrips: number;
  completedTrips: number;
  cancelledTrips: number;
  totalPassengers: number;
}

export interface FleetReportData {
  vehicleId: string;
  registrationNumber: string;
  utilisationPercentage: number;
  maintenanceEvents: number;
  totalKm: number;
  status: string;
}

export interface DriverReportData {
  driverId: string;
  driverName: string;
  tripsCompleted: number;
  onTimeRate: number;
  avgTripDurationMinutes: number;
  totalPassengers: number;
}

export type ReportType = 'route' | 'daily' | 'fleet' | 'driver' | 'passenger';

export interface FilteredReportResponse {
  reportType: ReportType;
  filtersApplied: Record<string, unknown>;
  generatedAt: string;
  data: (RouteReportData | DailyReportData | FleetReportData | DriverReportData)[];
}

export interface PassengerTripRecord {
  tripId: string;
  tripDate: string;
  routeName: string;
  boardingStop?: string;
  alightingStop?: string;
  scheduledDeparture?: string;
  actualDeparture?: string;
  scheduledArrival?: string;
  actualArrival?: string;
  onTime: boolean;
}

export interface PassengerReportResponse {
  passengerId: string;
  passengerName: string;
  dateFrom: string;
  dateTo: string;
  generatedAt: string;
  message?: string;
  data: PassengerTripRecord[];
}

// Arrivals
export interface ArrivalEstimate {
  vehicleId: string;
  registrationNumber: string;
  routeId: string;
  routeName: string;
  distanceToStopKm: number;
  currentSpeedKmh: number;
  etaMinutes: number | null;
  estimatedArrivalTime: string | null;
  status: string;
  currentOccupancy: number;
  seatingCapacity: number;
  remainingSeats: number;
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
  engineStatus?: EngineStatus;
  nextStopName?: string;
  progressPct?: number;
};

export type WsMessage = {
  type: 'vehicle_positions';
  vehicles: WsVehiclePosition[];
};
