import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { mockAnalytics, mockVehicles, mockTrips, mockRoutes } from '../../lib/mock-data';
import { TrendingUp, TrendingDown, Clock, DollarSign, Users, Fuel } from 'lucide-react';

export function Analytics() {
  // Fleet status distribution
  const fleetStatusData = [
    { name: 'Active', value: mockVehicles.filter(v => v.status === 'active').length, color: '#10B981' },
    { name: 'Idle', value: mockVehicles.filter(v => v.status === 'idle').length, color: '#F59E0B' },
    { name: 'Maintenance', value: mockVehicles.filter(v => v.status === 'maintenance').length, color: '#EF4444' },
    { name: 'Offline', value: mockVehicles.filter(v => v.status === 'offline').length, color: '#6B7280' },
  ];

  // Route performance
  const routePerformanceData = mockRoutes.map(route => {
    const routeTrips = mockTrips.filter(t => t.routeId === route.id);
    const totalPassengers = routeTrips.reduce((sum, t) => sum + t.passengers, 0);
    return {
      name: route.number,
      passengers: totalPassengers,
      trips: routeTrips.length,
    };
  });

  // Calculate key metrics
  const totalRevenue = mockAnalytics.reduce((sum, a) => sum + a.revenue, 0);
  const avgOnTime = Math.round(mockAnalytics.reduce((sum, a) => sum + a.onTimePercentage, 0) / mockAnalytics.length);
  const totalPassengers = mockAnalytics.reduce((sum, a) => sum + a.totalPassengers, 0);
  const totalFuel = mockAnalytics.reduce((sum, a) => sum + a.fuelConsumption, 0);

  // Trend calculations
  const revenueChange = mockAnalytics.length > 1 
    ? ((mockAnalytics[mockAnalytics.length - 1].revenue - mockAnalytics[0].revenue) / mockAnalytics[0].revenue * 100).toFixed(1)
    : 0;
  const passengerChange = mockAnalytics.length > 1
    ? ((mockAnalytics[mockAnalytics.length - 1].totalPassengers - mockAnalytics[0].totalPassengers) / mockAnalytics[0].totalPassengers * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics & Reporting</h1>
        <p className="text-slate-600">Performance metrics and operational insights</p>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Revenue (7 Days)</CardTitle>
            <DollarSign className="size-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(totalRevenue / 1000000).toFixed(1)}M RWF</div>
            <div className="flex items-center gap-1 text-xs mt-1">
              {Number(revenueChange) >= 0 ? (
                <>
                  <TrendingUp className="size-3 text-green-600" />
                  <span className="text-green-600">+{revenueChange}%</span>
                </>
              ) : (
                <>
                  <TrendingDown className="size-3 text-red-600" />
                  <span className="text-red-600">{revenueChange}%</span>
                </>
              )}
              <span className="text-slate-500">vs last week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Avg On-Time Performance</CardTitle>
            <Clock className="size-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgOnTime}%</div>
            <p className="text-xs text-slate-500 mt-1">
              Across all routes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Passengers (7 Days)</CardTitle>
            <Users className="size-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(totalPassengers / 1000).toFixed(1)}K</div>
            <div className="flex items-center gap-1 text-xs mt-1">
              {Number(passengerChange) >= 0 ? (
                <>
                  <TrendingUp className="size-3 text-green-600" />
                  <span className="text-green-600">+{passengerChange}%</span>
                </>
              ) : (
                <>
                  <TrendingDown className="size-3 text-red-600" />
                  <span className="text-red-600">{passengerChange}%</span>
                </>
              )}
              <span className="text-slate-500">vs last week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Fuel Consumption (7 Days)</CardTitle>
            <Fuel className="size-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFuel}L</div>
            <p className="text-xs text-slate-500 mt-1">
              Avg {Math.round(totalFuel / 7)}L per day
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="trends" className="space-y-4">
        <TabsList>
          <TabsTrigger value="trends">Operational Trends</TabsTrigger>
          <TabsTrigger value="routes">Route Performance</TabsTrigger>
          <TabsTrigger value="fleet">Fleet Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Daily Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={mockAnalytics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="onTimePercentage" stroke="#10B981" name="On-Time %" />
                    <Line type="monotone" dataKey="totalTrips" stroke="#3B82F6" name="Total Trips" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Revenue & Passengers</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mockAnalytics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="revenue" fill="#10B981" name="Revenue (RWF)" />
                    <Bar yAxisId="right" dataKey="totalPassengers" fill="#3B82F6" name="Passengers" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Fuel Consumption Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={mockAnalytics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="fuelConsumption" stroke="#F59E0B" name="Fuel (Liters)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="routes" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Route Performance Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={routePerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="passengers" fill="#3B82F6" name="Total Passengers" />
                    <Bar dataKey="trips" fill="#10B981" name="Total Trips" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Route Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockRoutes.map(route => {
                    const routeTrips = mockTrips.filter(t => t.routeId === route.id);
                    const totalPassengers = routeTrips.reduce((sum, t) => sum + t.passengers, 0);
                    const avgPassengers = routeTrips.length > 0 ? Math.round(totalPassengers / routeTrips.length) : 0;
                    
                    return (
                      <div key={route.id} className="border-b pb-3 last:border-0">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div 
                              className="size-3 rounded-full"
                              style={{ backgroundColor: route.color }}
                            />
                            <span className="font-medium">Route {route.number}</span>
                          </div>
                          <span className="text-sm text-slate-600">{route.name}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-sm">
                          <div>
                            <p className="text-xs text-slate-500">Trips</p>
                            <p className="font-medium">{routeTrips.length}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500">Passengers</p>
                            <p className="font-medium">{totalPassengers}</p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500">Avg/Trip</p>
                            <p className="font-medium">{avgPassengers}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="fleet" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Fleet Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={fleetStatusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {fleetStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fleet Health Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockVehicles.map(vehicle => (
                    <div key={vehicle.id} className="border-b pb-3 last:border-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">{vehicle.registrationNumber}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          vehicle.engineStatus === 'good' ? 'bg-green-100 text-green-700' :
                          vehicle.engineStatus === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {vehicle.engineStatus}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-slate-500">Fuel Level</span>
                            <span className="text-xs">{vehicle.fuel}%</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-slate-200">
                            <div
                              className={`h-full rounded-full ${
                                vehicle.fuel > 50 ? 'bg-green-500' :
                                vehicle.fuel > 25 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${vehicle.fuel}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
