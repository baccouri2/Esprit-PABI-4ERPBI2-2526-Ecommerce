import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { TranslationService } from '../../services/translation.service';

interface Order {
  id: number;
  id_order: string;
  order_status: string;
  date_commande: string;
  fk_delivery: number;
  delivery_num_bl?: string;
  delivery_company?: string;
  delivery_cost?: number;
  item_count?: number;
  total_amount?: number;
  client_name?: string;
  client_mf?: string;
  client_address?: string;
  client_phone?: string;
  items?: OrderItem[];
}

interface OrderItem {
  id: number;
  reference: string;
  description: string;
  unit_price: number;
  quantity: number;
  discount: number;
  total_price: number;
}

@Component({
  selector: 'app-orders',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './orders.component.html',
  styleUrls: ['./orders.component.scss']
})
export class OrdersComponent implements OnInit {
  // ── Permissions ────────────────────────────────────────────────────────────
  permissions = {
    create: false,
    read: false,
    update: false,
    delete: false
  };

  orders: Order[] = [];
  filteredOrders: Order[] = [];
  statuses: string[] = [];
  
  searchQuery = '';
  selectedStatus = '';
  loading = false;
  error = '';
  
  showModal = false;
  modalMode: 'create' | 'edit' | 'view' = 'create';
  selectedOrder: Order | null = null;
  
  formData = {
    id_order: '',
    order_status: 'En attente',
    date_commande: new Date().toISOString().split('T')[0],
    fk_delivery: null as number | null
  };

  constructor(
    private api: ApiService, 
    private auth: AuthService,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.permissions = this.auth.getOrderPermissions();
    this.loadStatuses();
    this.loadOrders();
  }

  loadStatuses() {
    this.api.getOrderStatuses().subscribe({
      next: (res: any) => {
        if (res.success) {
          this.statuses = res.statuses;
        }
      },
      error: (err) => console.error('Error loading statuses:', err)
    });
  }

  loadOrders() {
    this.loading = true;
    this.error = '';
    
    console.log('🔍 Loading orders...', { searchQuery: this.searchQuery, selectedStatus: this.selectedStatus });
    
    this.api.getAllOrders(this.searchQuery, this.selectedStatus).subscribe({
      next: (res: any) => {
        this.loading = false;
        console.log('✅ Orders loaded:', res);
        if (res.success) {
          this.orders = res.orders;
          this.filteredOrders = res.orders;
          console.log(`📦 Total orders: ${this.orders.length}`);
        } else {
          this.error = res.error || 'Failed to load orders';
          console.error('❌ Error in response:', this.error);
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to load orders';
        console.error('❌ HTTP Error:', err);
      }
    });
  }

  onSearch() {
    this.loadOrders();
  }

  onFilterStatus() {
    this.loadOrders();
  }

  clearFilters() {
    this.searchQuery = '';
    this.selectedStatus = '';
    this.loadOrders();
  }

  openCreateModal() {
    this.modalMode = 'create';
    this.formData = {
      id_order: '',
      order_status: 'En attente',
      date_commande: new Date().toISOString().split('T')[0],
      fk_delivery: null
    };
    this.showModal = true;
  }

  openEditModal(order: Order) {
    this.modalMode = 'edit';
    this.selectedOrder = order;
    this.formData = {
      id_order: order.id_order,
      order_status: order.order_status,
      date_commande: order.date_commande?.split(' ')[0] || new Date().toISOString().split('T')[0],
      fk_delivery: order.fk_delivery
    };
    this.showModal = true;
  }

  openViewModal(order: Order) {
    this.loading = true;
    this.api.getOrder(order.id).subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.selectedOrder = res.order;
          this.modalMode = 'view';
          this.showModal = true;
        } else {
          this.error = res.error || 'Failed to load order details';
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to load order details';
      }
    });
  }

  closeModal() {
    this.showModal = false;
    this.selectedOrder = null;
  }

  saveOrder() {
    if (!this.formData.id_order) {
      this.error = 'Order ID is required';
      return;
    }

    this.loading = true;
    this.error = '';

    const request = this.modalMode === 'create'
      ? this.api.createOrder(this.formData)
      : this.api.updateOrder(this.selectedOrder!.id, this.formData);

    request.subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.closeModal();
          this.loadOrders();
        } else {
          this.error = res.error || 'Failed to save order';
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to save order';
      }
    });
  }

  deleteOrder(order: Order) {
    if (!confirm(`Are you sure you want to delete order ${order.id_order}?`)) {
      return;
    }

    this.loading = true;
    this.error = '';

    this.api.deleteOrder(order.id).subscribe({
      next: (res: any) => {
        this.loading = false;
        if (res.success) {
          this.loadOrders();
        } else {
          this.error = res.error || 'Failed to delete order';
        }
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to delete order';
      }
    });
  }

  downloadInvoice(order: Order) {
    this.loading = true;
    this.error = '';

    this.api.downloadInvoice(order.id).subscribe({
      next: (blob: Blob) => {
        this.loading = false;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Facture_${order.id_order}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.message || 'Failed to download invoice';
      }
    });
  }

  getStatusClass(status: string): string {
    const statusMap: { [key: string]: string } = {
      'En attente': 'status-pending',
      'Confirmée': 'status-confirmed',
      'En préparation': 'status-preparing',
      'Expédiée': 'status-shipped',
      'Livrée': 'status-delivered',
      'Annulée': 'status-cancelled',
      'En cours': 'status-inprogress',
      'Terminée': 'status-completed'
    };
    return statusMap[status] || 'status-default';
  }
}
