import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard]
  },
  {
    path: 'assistant',
    loadComponent: () => import('./pages/ia-assistant/ia-assistant.component').then(m => m.IaAssistantComponent),
    canActivate: [authGuard]
  },
  {
    path: 'clients',
    loadComponent: () => import('./pages/clients/clients.component').then(m => m.ClientsComponent),
    canActivate: [authGuard]
  },
  {
    path: 'suppliers',
    loadComponent: () => import('./pages/suppliers/suppliers.component').then(m => m.SuppliersComponent),
    canActivate: [authGuard]
  },
  {
    path: 'products',
    loadComponent: () => import('./pages/products/products.component').then(m => m.ProductsComponent),
    canActivate: [authGuard]
  },
  {
    path: 'orders',
    loadComponent: () => import('./pages/orders/orders.component').then(m => m.OrdersComponent),
    canActivate: [authGuard]
  },
  {
    path: 'crm',
    loadComponent: () => import('./pages/crm/crm.component').then(m => m.CrmComponent),
    canActivate: [authGuard]
  },
  // Keep individual routes accessible for direct navigation / guard checks
  { path: 'forecast',        redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'segmentation',    redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'anomaly',         redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'promotion',       redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'recommendations', redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'sentiment',       redirectTo: '/assistant', pathMatch: 'full' },
  { path: 'competition',     redirectTo: '/assistant', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' }
];
