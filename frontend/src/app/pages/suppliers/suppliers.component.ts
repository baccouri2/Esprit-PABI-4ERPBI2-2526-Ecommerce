import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';

type ModalMode = 'create' | 'edit' | null;

@Component({
  selector: 'app-suppliers',
  standalone: true,
  imports: [CommonModule, FormsModule, SdgFooterComponent],
  templateUrl: './suppliers.component.html',
  styleUrls: ['./suppliers.component.scss']
})
export class SuppliersComponent implements OnInit {
  // ── Permissions ────────────────────────────────────────────────────────────
  permissions = {
    create: false,
    read: false,
    update: false,
    delete: false
  };

  suppliers:  any[] = [];
  loading     = false;
  error       = '';
  success     = '';
  searchQ     = '';

  modalMode:  ModalMode = null;
  saving      = false;
  modalError  = '';
  editId      = 0;

  form = { name_supplier: '', company: '', payment_method: '' };

  paymentMethods = ['Espèces', 'Virement', 'Chèque', 'Carte bancaire', 'Traite'];

  deleteTarget: any = null;
  deleting     = false;

  constructor(
    private api: ApiService, 
    private auth: AuthService,
    public translate: TranslationService
  ) {}

  ngOnInit() { 
    this.permissions = this.auth.getSupplierPermissions();
    this.load(); 
  }

  load() {
    this.loading = true;
    this.error   = '';
    this.api.getAllSuppliers(this.searchQ).subscribe({
      next: (res) => { this.suppliers = res.suppliers || []; this.loading = false; },
      error: (err) => { this.error = err.error?.error || 'Failed to load suppliers'; this.loading = false; }
    });
  }

  onSearch() { this.load(); }

  openCreate() {
    this.modalMode  = 'create';
    this.modalError = '';
    this.form = { name_supplier: '', company: '', payment_method: 'Espèces' };
  }

  openEdit(s: any) {
    this.modalMode  = 'edit';
    this.editId     = s.id;
    this.modalError = '';
    this.form = {
      name_supplier:  s.name_supplier,
      company:        s.company,
      payment_method: s.payment_method
    };
  }

  closeModal() { this.modalMode = null; }

  save() {
    if (!this.form.name_supplier.trim()) { this.modalError = 'Name is required'; return; }
    if (!this.form.company.trim())       { this.modalError = 'Company is required'; return; }
    if (!this.form.payment_method)       { this.modalError = 'Payment method is required'; return; }

    this.saving     = true;
    this.modalError = '';

    const obs = this.modalMode === 'create'
      ? this.api.createSupplier(this.form)
      : this.api.updateSupplier(this.editId, this.form);

    obs.subscribe({
      next: (res: any) => {
        this.saving    = false;
        this.modalMode = null;
        this.success   = res.message || 'Saved';
        this.load();
        setTimeout(() => this.success = '', 3000);
      },
      error: (err: any) => {
        this.saving     = false;
        this.modalError = err.error?.error || 'Save failed';
      }
    });
  }

  confirmDelete(s: any) { this.deleteTarget = s; }
  cancelDelete()        { this.deleteTarget = null; }

  doDelete() {
    if (!this.deleteTarget) return;
    this.deleting = true;
    this.api.deleteSupplier(this.deleteTarget.id).subscribe({
      next: (res: any) => {
        this.deleting     = false;
        this.deleteTarget = null;
        this.success      = res.message || 'Deleted';
        this.load();
        setTimeout(() => this.success = '', 3000);
      },
      error: (err: any) => {
        this.deleting     = false;
        this.error        = err.error?.error || 'Delete failed';
        this.deleteTarget = null;
      }
    });
  }

  get withPurchases() { return this.suppliers.filter(s => s.purchase_count > 0).length; }

  paymentBadgeClass(method: string): string {
    const map: Record<string, string> = {
      'Espèces':        'badge-cash',
      'Virement':       'badge-wire',
      'Chèque':         'badge-check',
      'Carte bancaire': 'badge-card',
      'Traite':         'badge-draft'
    };
    return map[method] || 'badge-default';
  }
}
