import { createBrowserRouter, Navigate } from 'react-router';
import React from 'react';
import { MainLayout } from './components/layout/MainLayout';
import { LoginPage } from './components/pages/LoginPage';
import { RegisterPage } from './components/pages/RegisterPage';
import { AcceptInvitePage } from './components/pages/AcceptInvitePage';
import { RoleHomeRedirect } from './components/RoleHomeRedirect';
import { SuperadminRoute } from './components/SuperadminRoute';
import { SuperadminPortal } from './components/pages/SuperadminPortal';
import { VehicleTracking } from './components/pages/VehicleTracking';
import { FleetManagement } from './components/pages/FleetManagement';
import { RouteManagement } from './components/pages/RouteManagement';
import { ArrivalTimes } from './components/pages/ArrivalTimes';
import { PassengerApp } from './components/pages/PassengerApp';
import { Dispatch } from './components/pages/Dispatch';
import { Drivers } from './components/pages/Drivers';
import { Maintenance } from './components/pages/Maintenance';
import { Analytics } from './components/pages/Analytics';
import { Alerts } from './components/pages/Alerts';
import { Administration } from './components/pages/Administration';
import { Security } from './components/pages/Security';
import { ProtectedRoute } from './components/ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: '/login',
    Component: LoginPage,
  },
  {
    path: '/register',
    Component: RegisterPage,
  },
  {
    path: '/accept-invite',
    Component: AcceptInvitePage,
  },
  {
    path: '/',
    element: <ProtectedRoute><MainLayout /></ProtectedRoute>,
    children: [
      { index: true, Component: RoleHomeRedirect },
      {
        path: 'superadmin',
        element: (
          <SuperadminRoute>
            <Navigate to="/superadmin/analytics" replace />
          </SuperadminRoute>
        ),
      },
      {
        path: 'superadmin/:tab',
        element: (
          <SuperadminRoute>
            <SuperadminPortal />
          </SuperadminRoute>
        ),
      },
      { path: 'tracking', Component: VehicleTracking },
      { path: 'fleet', Component: FleetManagement },
      { path: 'routes', Component: RouteManagement },
      { path: 'arrivals', Component: ArrivalTimes },
      { path: 'passenger', Component: PassengerApp },
      { path: 'dispatch', Component: Dispatch },
      { path: 'drivers', Component: Drivers },
      { path: 'maintenance', Component: Maintenance },
      { path: 'analytics', Component: Analytics },
      { path: 'alerts', Component: Alerts },
      { path: 'admin', Component: Administration },
      { path: 'security', Component: Security },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
