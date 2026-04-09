// Mock data for the transport system (Kigali, Rwanda coordinates)
import type { Vehicle, Route, Stop, Driver, Trip, MaintenanceRecord, Alert, Analytics, User } from './types';

// Mock users
export const mockUsers: User[] = [
  {
    id: 'user-1',
    email: 'admin@transport.rw',
    fullName: 'Jean Claude Mugabo',
    role: 'admin',
    phone: '+250788123456',
    company: 'Rwanda Transport Authority'
  },
  {
    id: 'user-2',
    email: 'operator@transport.rw',
    fullName: 'Marie Umutesi',
    role: 'operator',
    phone: '+250788234567',
    company: 'Kigali Express'
  },
  {
    id: 'user-3',
    email: 'dispatcher@transport.rw',
    fullName: 'Paul Nkunda',
    role: 'dispatcher',
    phone: '+250788345678',
    company: 'Kigali Express'
  }
];

// Kigali bus stops
export const mockStops: Stop[] = [
  { id: 'stop-1', name: 'Nyabugogo', location: { lat: -1.9396, lng: 30.0585 }, order: 1 },
  { id: 'stop-2', name: 'Kacyiru', location: { lat: -1.9453, lng: 30.0907 }, order: 2 },
  { id: 'stop-3', name: 'Remera', location: { lat: -1.9565, lng: 30.1141 }, order: 3 },
  { id: 'stop-4', name: 'Kimironko', location: { lat: -1.9450, lng: 30.1290 }, order: 4 },
  { id: 'stop-5', name: 'Gisozi', location: { lat: -1.9282, lng: 30.1118 }, order: 5 },
  { id: 'stop-6', name: 'City Centre', location: { lat: -1.9536, lng: 30.0606 }, order: 1 },
  { id: 'stop-7', name: 'Kiyovu', location: { lat: -1.9650, lng: 30.0550 }, order: 2 },
  { id: 'stop-8', name: 'Nyamirambo', location: { lat: -1.9781, lng: 30.0447 }, order: 3 },
  { id: 'stop-9', name: 'Gikondo', location: { lat: -2.0032, lng: 30.0584 }, order: 4 },
  { id: 'stop-10', name: 'Kanombe', location: { lat: -1.9646, lng: 30.1291 }, order: 1 },
  { id: 'stop-11', name: 'Kicukiro', location: { lat: -1.9908, lng: 30.1021 }, order: 2 },
  { id: 'stop-12', name: 'Sonatube', location: { lat: -2.0012, lng: 30.0899 }, order: 3 },
];

// Routes
export const mockRoutes: Route[] = [
  {
    id: 'route-1',
    name: 'Nyabugogo - Kimironko',
    number: '101',
    stops: [mockStops[0], mockStops[1], mockStops[2], mockStops[3]],
    distance: 12.5,
    duration: 35,
    active: true,
    color: '#3B82F6'
  },
  {
    id: 'route-2',
    name: 'City Centre - Nyamirambo',
    number: '202',
    stops: [mockStops[5], mockStops[6], mockStops[7], mockStops[8]],
    distance: 8.3,
    duration: 25,
    active: true,
    color: '#10B981'
  },
  {
    id: 'route-3',
    name: 'Kanombe - Kicukiro',
    number: '303',
    stops: [mockStops[9], mockStops[10], mockStops[11]],
    distance: 10.2,
    duration: 30,
    active: true,
    color: '#F59E0B'
  },
  {
    id: 'route-4',
    name: 'Nyabugogo - Gisozi',
    number: '104',
    stops: [mockStops[0], mockStops[1], mockStops[4]],
    distance: 9.8,
    duration: 28,
    active: true,
    color: '#EF4444'
  }
];

// Vehicles
export const mockVehicles: Vehicle[] = [
  {
    id: 'veh-1',
    registrationNumber: 'RAD 001 A',
    model: 'Yutong ZK6120',
    capacity: 60,
    status: 'active',
    currentLocation: { lat: -1.9450, lng: 30.0907 },
    speed: 35,
    heading: 90,
    routeId: 'route-1',
    driverId: 'drv-1',
    lastUpdate: new Date().toISOString(),
    fuel: 75,
    engineStatus: 'good'
  },
  {
    id: 'veh-2',
    registrationNumber: 'RAD 002 B',
    model: 'Higer KLQ6129',
    capacity: 55,
    status: 'active',
    currentLocation: { lat: -1.9650, lng: 30.0550 },
    speed: 28,
    heading: 180,
    routeId: 'route-2',
    driverId: 'drv-2',
    lastUpdate: new Date().toISOString(),
    fuel: 60,
    engineStatus: 'good'
  },
  {
    id: 'veh-3',
    registrationNumber: 'RAD 003 C',
    model: 'King Long XMQ6127',
    capacity: 58,
    status: 'active',
    currentLocation: { lat: -1.9908, lng: 30.1021 },
    speed: 42,
    heading: 45,
    routeId: 'route-3',
    driverId: 'drv-3',
    lastUpdate: new Date().toISOString(),
    fuel: 85,
    engineStatus: 'good'
  },
  {
    id: 'veh-4',
    registrationNumber: 'RAD 004 D',
    model: 'Yutong ZK6120',
    capacity: 60,
    status: 'idle',
    currentLocation: { lat: -1.9396, lng: 30.0585 },
    speed: 0,
    heading: 0,
    routeId: null,
    driverId: null,
    lastUpdate: new Date().toISOString(),
    fuel: 90,
    engineStatus: 'good'
  },
  {
    id: 'veh-5',
    registrationNumber: 'RAD 005 E',
    model: 'Higer KLQ6129',
    capacity: 55,
    status: 'maintenance',
    currentLocation: { lat: -1.9396, lng: 30.0585 },
    speed: 0,
    heading: 0,
    routeId: null,
    driverId: null,
    lastUpdate: new Date(Date.now() - 3600000).toISOString(),
    fuel: 45,
    engineStatus: 'warning'
  },
  {
    id: 'veh-6',
    registrationNumber: 'RAD 006 F',
    model: 'King Long XMQ6127',
    capacity: 58,
    status: 'active',
    currentLocation: { lat: -1.9282, lng: 30.1118 },
    speed: 32,
    heading: 270,
    routeId: 'route-4',
    driverId: 'drv-4',
    lastUpdate: new Date().toISOString(),
    fuel: 70,
    engineStatus: 'good'
  }
];

// Drivers
export const mockDrivers: Driver[] = [
  {
    id: 'drv-1',
    name: 'Eric Nsabimana',
    licenseNumber: 'DL-001-2020',
    phone: '+250788111222',
    rating: 4.8,
    totalTrips: 1250,
    status: 'on-trip',
    vehicleId: 'veh-1',
    certificationExpiry: '2026-12-31'
  },
  {
    id: 'drv-2',
    name: 'Grace Mukamana',
    licenseNumber: 'DL-002-2019',
    phone: '+250788222333',
    rating: 4.9,
    totalTrips: 1480,
    status: 'on-trip',
    vehicleId: 'veh-2',
    certificationExpiry: '2026-08-15'
  },
  {
    id: 'drv-3',
    name: 'Daniel Habimana',
    licenseNumber: 'DL-003-2021',
    phone: '+250788333444',
    rating: 4.7,
    totalTrips: 980,
    status: 'on-trip',
    vehicleId: 'veh-3',
    certificationExpiry: '2027-03-20'
  },
  {
    id: 'drv-4',
    name: 'Sarah Uwera',
    licenseNumber: 'DL-004-2020',
    phone: '+250788444555',
    rating: 4.85,
    totalTrips: 1320,
    status: 'on-trip',
    vehicleId: 'veh-6',
    certificationExpiry: '2026-11-10'
  },
  {
    id: 'drv-5',
    name: 'Patrick Niyonzima',
    licenseNumber: 'DL-005-2022',
    phone: '+250788555666',
    rating: 4.6,
    totalTrips: 750,
    status: 'available',
    vehicleId: null,
    certificationExpiry: '2027-06-30'
  }
];

// Trips
export const mockTrips: Trip[] = [
  {
    id: 'trip-1',
    vehicleId: 'veh-1',
    routeId: 'route-1',
    driverId: 'drv-1',
    scheduledStart: '2026-02-27T08:00:00',
    actualStart: '2026-02-27T08:02:00',
    scheduledEnd: '2026-02-27T08:35:00',
    actualEnd: null,
    status: 'active',
    passengers: 42,
    delay: 2
  },
  {
    id: 'trip-2',
    vehicleId: 'veh-2',
    routeId: 'route-2',
    driverId: 'drv-2',
    scheduledStart: '2026-02-27T08:15:00',
    actualStart: '2026-02-27T08:15:00',
    scheduledEnd: '2026-02-27T08:40:00',
    actualEnd: null,
    status: 'active',
    passengers: 38,
    delay: 0
  },
  {
    id: 'trip-3',
    vehicleId: 'veh-3',
    routeId: 'route-3',
    driverId: 'drv-3',
    scheduledStart: '2026-02-27T07:45:00',
    actualStart: '2026-02-27T07:50:00',
    scheduledEnd: '2026-02-27T08:15:00',
    actualEnd: null,
    status: 'active',
    passengers: 45,
    delay: 5
  }
];

// Maintenance Records
export const mockMaintenanceRecords: MaintenanceRecord[] = [
  {
    id: 'maint-1',
    vehicleId: 'veh-5',
    type: 'repair',
    description: 'Engine oil leak repair',
    scheduledDate: '2026-02-27',
    completedDate: null,
    cost: 150000,
    status: 'in-progress',
    nextDue: null
  },
  {
    id: 'maint-2',
    vehicleId: 'veh-1',
    type: 'routine',
    description: 'Regular service - oil change',
    scheduledDate: '2026-03-05',
    completedDate: null,
    cost: 80000,
    status: 'scheduled',
    nextDue: '2026-06-05'
  },
  {
    id: 'maint-3',
    vehicleId: 'veh-2',
    type: 'inspection',
    description: 'Annual safety inspection',
    scheduledDate: '2026-03-10',
    completedDate: null,
    cost: 50000,
    status: 'scheduled',
    nextDue: '2027-03-10'
  },
  {
    id: 'maint-4',
    vehicleId: 'veh-4',
    type: 'routine',
    description: 'Tire replacement',
    scheduledDate: '2026-02-20',
    completedDate: '2026-02-20',
    cost: 240000,
    status: 'completed',
    nextDue: '2026-08-20'
  }
];

// Alerts
export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    type: 'delay',
    severity: 'medium',
    title: 'Route 303 Delay',
    message: 'Vehicle RAD 003 C is running 5 minutes behind schedule',
    vehicleId: 'veh-3',
    driverId: 'drv-3',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    acknowledged: false
  },
  {
    id: 'alert-2',
    type: 'maintenance',
    severity: 'high',
    title: 'Maintenance Due',
    message: 'Vehicle RAD 001 A is due for routine service in 7 days',
    vehicleId: 'veh-1',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: false
  },
  {
    id: 'alert-3',
    type: 'breakdown',
    severity: 'critical',
    title: 'Vehicle in Maintenance',
    message: 'Vehicle RAD 005 E is currently undergoing repairs for engine oil leak',
    vehicleId: 'veh-5',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    acknowledged: true
  },
  {
    id: 'alert-4',
    type: 'info',
    severity: 'low',
    title: 'New Driver Assignment',
    message: 'Driver Patrick Niyonzima is now available for trip assignment',
    driverId: 'drv-5',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    acknowledged: false
  }
];

// Analytics data (last 7 days)
export const mockAnalytics: Analytics[] = [
  {
    date: '2026-02-21',
    totalTrips: 145,
    onTimePercentage: 92,
    avgDelay: 3.2,
    totalPassengers: 5820,
    fuelConsumption: 840,
    revenue: 2910000
  },
  {
    date: '2026-02-22',
    totalTrips: 138,
    onTimePercentage: 88,
    avgDelay: 4.1,
    totalPassengers: 5520,
    fuelConsumption: 810,
    revenue: 2760000
  },
  {
    date: '2026-02-23',
    totalTrips: 142,
    onTimePercentage: 90,
    avgDelay: 3.5,
    totalPassengers: 5680,
    fuelConsumption: 825,
    revenue: 2840000
  },
  {
    date: '2026-02-24',
    totalTrips: 155,
    onTimePercentage: 94,
    avgDelay: 2.8,
    totalPassengers: 6200,
    fuelConsumption: 870,
    revenue: 3100000
  },
  {
    date: '2026-02-25',
    totalTrips: 148,
    onTimePercentage: 91,
    avgDelay: 3.3,
    totalPassengers: 5920,
    fuelConsumption: 850,
    revenue: 2960000
  },
  {
    date: '2026-02-26',
    totalTrips: 151,
    onTimePercentage: 93,
    avgDelay: 2.9,
    totalPassengers: 6040,
    fuelConsumption: 860,
    revenue: 3020000
  },
  {
    date: '2026-02-27',
    totalTrips: 78,
    onTimePercentage: 95,
    avgDelay: 2.5,
    totalPassengers: 3120,
    fuelConsumption: 445,
    revenue: 1560000
  }
];
