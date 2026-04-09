import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { mockRoutes, mockStops, mockVehicles } from '../../lib/mock-data';
import { MapPin, Clock, Navigation, Star, Heart, Search, Bus } from 'lucide-react';

export function PassengerApp() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStop, setSelectedStop] = useState<string | null>(null);
  const [favoriteStops] = useState<string[]>(['stop-1', 'stop-3', 'stop-6']);

  const filteredStops = mockStops.filter(stop =>
    stop.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate estimated arrival times (simulated)
  const getEstimatedArrival = (stopId: string, routeId: string) => {
    const vehicle = mockVehicles.find(v => v.routeId === routeId && v.status === 'active');
    if (!vehicle) return null;
    
    // Simulate ETA calculation
    const baseETA = Math.floor(Math.random() * 15) + 5;
    return baseETA;
  };

  const stopArrivals = selectedStop 
    ? mockRoutes
        .filter(route => route.stops.some(s => s.id === selectedStop))
        .map(route => {
          const eta = getEstimatedArrival(selectedStop, route.id);
          const vehicle = mockVehicles.find(v => v.routeId === route.id && v.status === 'active');
          return { route, eta, vehicle };
        })
        .filter(item => item.eta !== null)
    : [];

  return (
    <div className="max-w-5xl mx-auto pb-20 px-4 space-y-6">
      {/* Passenger App Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">Rwanda Transport</h1>
            <p className="text-sm text-blue-100">Passenger Information</p>
          </div>
          <Bus className="size-10" />
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-blue-300" />
          <Input
            placeholder="Search for bus stops..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-blue-200"
          />
        </div>
      </div>

      {/* Main content: stops list + side panel */}
      <div className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        {/* Left: Favorite & Nearby Stops */}
        <div className="space-y-6">
          {/* Favorite Stops */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Heart className="size-5 text-red-500" />
                Favorite Stops
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {mockStops
                  .filter(stop => favoriteStops.includes(stop.id))
                  .map(stop => (
                    <Button
                      key={stop.id}
                      variant={selectedStop === stop.id ? "default" : "outline"}
                      className="w-full justify-start"
                      onClick={() => setSelectedStop(stop.id)}
                    >
                      <MapPin className="mr-2 size-4" />
                      {stop.name}
                    </Button>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Nearby Stops */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Navigation className="size-5 text-blue-600" />
                {searchTerm ? 'Search Results' : 'Nearby Stops'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredStops.map(stop => {
                  const routesAtStop = mockRoutes.filter(r => 
                    r.stops.some(s => s.id === stop.id)
                  );
                  
                  return (
                    <div
                      key={stop.id}
                      onClick={() => setSelectedStop(stop.id)}
                      className={`cursor-pointer rounded-lg border p-3 transition-colors ${
                        selectedStop === stop.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <MapPin className="size-4 text-slate-400" />
                            <p className="font-medium">{stop.name}</p>
                          </div>
                          <p className="text-xs text-slate-500 mt-1 ml-6">
                            {routesAtStop.length} route{routesAtStop.length !== 1 ? 's' : ''} available
                          </p>
                          <div className="flex flex-wrap gap-1 mt-2 ml-6">
                            {routesAtStop.map(route => (
                              <Badge key={route.id} variant="secondary" className="text-xs">
                                {route.number}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        {favoriteStops.includes(stop.id) && (
                          <Heart className="size-4 fill-red-500 text-red-500" />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Next Arrivals + Service Info */}
        <div className="space-y-6">
          {/* Arrival Times for Selected Stop */}
          {selectedStop && stopArrivals.length > 0 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="size-5 text-blue-600" />
                  Next Arrivals at {mockStops.find(s => s.id === selectedStop)?.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stopArrivals.map(({ route, eta, vehicle }) => (
                    <div key={route.id} className="rounded-lg bg-white p-4 shadow-sm">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge style={{ backgroundColor: route.color }} className="text-white">
                              Route {route.number}
                            </Badge>
                            <p className="font-medium">{route.name}</p>
                          </div>
                          {vehicle && (
                            <p className="text-xs text-slate-500 mt-1">
                              Vehicle: {vehicle.registrationNumber}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-blue-600">{eta}</p>
                          <p className="text-xs text-slate-500">minutes</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mt-3 pt-3 border-t">
                        <div className="flex items-center gap-4 text-xs text-slate-600">
                          <span>{route.distance} km</span>
                          <span>~{route.duration} min trip</span>
                        </div>
                        <Button size="sm" variant="outline">
                          View Route
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Quick Info / Service Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Service Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <Clock className="size-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="font-medium">Operating Hours</p>
                  <p className="text-xs text-slate-600">Monday - Sunday: 5:00 AM - 11:00 PM</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <Star className="size-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium">Fare Information</p>
                  <p className="text-xs text-slate-600">Base fare: 200 RWF | Distance-based pricing</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <MapPin className="size-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium">Coverage Area</p>
                  <p className="text-xs text-slate-600">Kigali City - All major districts</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
