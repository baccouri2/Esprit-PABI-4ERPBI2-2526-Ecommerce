import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

export type UserRole = 'ceo' | 'sales_marketing' | 'logistics_finance';

export interface User {
  username: string;
  name: string;
  role: UserRole;
  avatar: string;
}

const USERS: Array<User & { password: string }> = [
  {
    username: 'hedir.zraga@esprit.tn',
    password: 'Sougui@CEO2024',
    name: 'Hedir Zraga (CEO)',
    role: 'ceo',
    avatar: 'HZ'
  },
  {
    username: 'sales',
    password: 'Sougui@Sales2024',
    name: 'Sales & Marketing Manager',
    role: 'sales_marketing',
    avatar: 'S'
  },
  {
    username: 'logistics',
    password: 'Sougui@Log2024',
    name: 'Logistics & Finance Manager',
    role: 'logistics_finance',
    avatar: 'L'
  }
];

// Page access permissions per role
export const PAGE_PERMISSIONS: Record<string, UserRole[]> = {
  'dashboard':       ['ceo', 'sales_marketing', 'logistics_finance'],
  'forecast':        ['ceo', 'sales_marketing'],
  'segmentation':    ['ceo', 'sales_marketing'],
  'anomaly':         ['ceo', 'logistics_finance'],
  'promotion':       ['ceo', 'sales_marketing', 'logistics_finance'],
  'recommendations': ['ceo'],
  'sentiment':       ['ceo', 'sales_marketing'],
  'competition':     ['ceo', 'sales_marketing', 'logistics_finance'],
  'clients':         ['ceo', 'sales_marketing', 'logistics_finance'],
  'suppliers':       ['ceo', 'logistics_finance'],
  'products':        ['ceo', 'sales_marketing', 'logistics_finance'],
  'orders':          ['ceo', 'sales_marketing', 'logistics_finance'],
  'crm':             ['ceo'], // CRM Odoo - CEO only
};

// CRUD permissions for clients page
export const CLIENT_PERMISSIONS: Record<UserRole, { create: boolean; read: boolean; update: boolean; delete: boolean }> = {
  'ceo': { create: true, read: true, update: true, delete: true },
  'sales_marketing': { create: true, read: true, update: true, delete: false },
  'logistics_finance': { create: false, read: true, update: false, delete: false },
};

// CRUD permissions for suppliers page
export const SUPPLIER_PERMISSIONS: Record<UserRole, { create: boolean; read: boolean; update: boolean; delete: boolean }> = {
  'ceo': { create: true, read: true, update: true, delete: true },
  'sales_marketing': { create: true, read: true, update: true, delete: false },
  'logistics_finance': { create: true, read: true, update: true, delete: false },
};

// CRUD permissions for orders page
export const ORDER_PERMISSIONS: Record<UserRole, { create: boolean; read: boolean; update: boolean; delete: boolean }> = {
  'ceo': { create: true, read: true, update: true, delete: true },
  'sales_marketing': { create: true, read: true, update: true, delete: true },
  'logistics_finance': { create: false, read: true, update: false, delete: false },
};

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly STORAGE_KEY = 'sougui_user';

  constructor(private router: Router) {}

  login(username: string, password: string): boolean {
    const user = USERS.find(
      u => u.username === username.toLowerCase() && u.password === password
    );
    if (user) {
      const { password: _, ...safeUser } = user;
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(safeUser));
      return true;
    }
    return false;
  }

  logout(): void {
    localStorage.removeItem(this.STORAGE_KEY);
    this.router.navigate(['/login']);
  }

  getCurrentUser(): User | null {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  isLoggedIn(): boolean {
    return !!this.getCurrentUser();
  }

  canAccess(page: string): boolean {
    const user = this.getCurrentUser();
    if (!user) return false;
    const allowed = PAGE_PERMISSIONS[page];
    if (!allowed) return true; // page not restricted
    return allowed.includes(user.role);
  }

  getAccessiblePages(): string[] {
    const user = this.getCurrentUser();
    if (!user) return [];
    return Object.entries(PAGE_PERMISSIONS)
      .filter(([, roles]) => roles.includes(user.role))
      .map(([page]) => page);
  }

  getDefaultPage(): string {
    return 'assistant';
  }

  // Get client CRUD permissions for current user
  getClientPermissions() {
    const user = this.getCurrentUser();
    if (!user) return { create: false, read: false, update: false, delete: false };
    return CLIENT_PERMISSIONS[user.role] || { create: false, read: false, update: false, delete: false };
  }

  // Get supplier CRUD permissions for current user
  getSupplierPermissions() {
    const user = this.getCurrentUser();
    if (!user) return { create: false, read: false, update: false, delete: false };
    return SUPPLIER_PERMISSIONS[user.role] || { create: false, read: false, update: false, delete: false };
  }

  // Get order CRUD permissions for current user
  getOrderPermissions() {
    const user = this.getCurrentUser();
    if (!user) return { create: false, read: false, update: false, delete: false };
    return ORDER_PERMISSIONS[user.role] || { create: false, read: false, update: false, delete: false };
  }

  // Get stored password for a user (for face recognition auto-login)
  getStoredPassword(username: string): string | null {
    // SECURITY: Only return password if face is registered
    const faceKey = `face_${username.toLowerCase()}`;
    const passwordKey = `face_password_${username.toLowerCase()}`;
    
    if (localStorage.getItem(faceKey) && localStorage.getItem(passwordKey)) {
      return localStorage.getItem(passwordKey);
    }
    
    return null;
  }

  // Validate credentials (for face enrollment)
  validateCredentials(username: string, password: string): boolean {
    const user = USERS.find(
      u => u.username === username.toLowerCase() && u.password === password
    );
    return !!user;
  }

  // Store password for face login (encrypted in production)
  storePasswordForFaceLogin(username: string, password: string): void {
    // SECURITY: In production, encrypt this password
    const passwordKey = `face_password_${username.toLowerCase()}`;
    localStorage.setItem(passwordKey, password);
  }

  // Clear face login data
  clearFaceLoginData(username: string): void {
    const passwordKey = `face_password_${username.toLowerCase()}`;
    localStorage.removeItem(passwordKey);
  }
}
