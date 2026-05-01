import { useState, useEffect, useRef } from 'react';
import type { Vehicle } from './types';
import { mockVehicles } from './mock-data';

// Simulate vehicle movement by updating positions slightly
export function useVehicleSimulation() {
  const [vehicles, setVehicles] = useState<Vehicle[]>(mockVehicles);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setVehicles(prevVehicles =>
        prevVehicles.map(vehicle => {
          if (vehicle.status !== 'active') return vehicle;

          // Small random movement for active vehicles (simulating GPS updates)
          const latChange = (Math.random() - 0.5) * 0.001; // ~100m
          const lngChange = (Math.random() - 0.5) * 0.001;

          return {
            ...vehicle,
            currentLocation: {
              lat: vehicle.currentLocation.lat + latChange,
              lng: vehicle.currentLocation.lng + lngChange,
            },
            speed: Math.max(0, vehicle.speed + (Math.random() - 0.5) * 5),
            lastUpdate: new Date().toISOString(),
          };
        })
      );
    }, 5000); // Update every 5 seconds (reduced frequency)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []);

  return vehicles;
}
