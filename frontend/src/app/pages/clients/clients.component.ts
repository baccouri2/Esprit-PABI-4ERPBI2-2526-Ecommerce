import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';

type ClientType = 'all' | 'b2b' | 'b2c';
type ModalMode  = 'create' | 'edit' | null;

@Component({
  selector: 'app-clients',
  standalone: true,
  imports: [CommonModule, FormsModule, SdgFooterComponent],
  templateUrl: './clients.component.html',
  styleUrls: ['./clients.component.scss']
})
export class ClientsComponent implements OnInit {
  // ── Permissions ────────────────────────────────────────────────────────────
  permissions = {
    create: false,
    read: false,
    update: false,
    delete: false
  };

  // ── State ──────────────────────────────────────────────────────────────────
  clients:     any[] = [];
  filtered:    any[] = [];
  loading      = false;
  error        = '';
  success      = '';

  // ── Filters ────────────────────────────────────────────────────────────────
  filterType: ClientType = 'all';
  searchQ    = '';

  // ── Modal ──────────────────────────────────────────────────────────────────
  modalMode:   ModalMode = null;
  modalType:   'b2b' | 'b2c' = 'b2b';
  saving       = false;
  modalError   = '';

  form = {
    MF:                 '',
    company:            '',
    first_name:         '',
    last_name:          '',
    date_participation: ''
  };
  editId = 0;

  // ── Delete confirm ─────────────────────────────────────────────────────────
  deleteTarget: any = null;
  deleting      = false;

  constructor(
    private api: ApiService, 
    private auth: AuthService,
    public translate: TranslationService
  ) {}

  ngOnInit() { 
    this.permissions = this.auth.getClientPermissions();
    this.load(); 
  }

  // ── Load ───────────────────────────────────────────────────────────────────
  load() {
    this.loading = true;
    this.error   = '';
    this.api.getAllClients('all').subscribe({
      next: (res) => {
        this.clients  = res.clients || [];
        this.applyFilter();
        this.loading  = false;
      },
      error: (err) => {
        this.error   = err.error?.error || 'Failed to load clients';
        this.loading = false;
      }
    });
  }

  applyFilter() {
    let list = this.clients;
    if (this.filterType !== 'all') {
      list = list.filter(c => c.type.toLowerCase() === this.filterType);
    }
    if (this.searchQ.trim()) {
      const q = this.searchQ.toLowerCase();
      list = list.filter(c =>
        (c.company || '').toLowerCase().includes(q) ||
        (c.full_name || '').toLowerCase().includes(q) ||
        (c.MF || '').toLowerCase().includes(q) ||
        String(c.id).includes(q)
      );
    }
    this.filtered = list;
  }

  onSearch() { this.applyFilter(); }
  onFilterType(t: ClientType) { this.filterType = t; this.applyFilter(); }

  // ── Create ─────────────────────────────────────────────────────────────────
  openCreate(type: 'b2b' | 'b2c') {
    this.modalMode  = 'create';
    this.modalType  = type;
    this.modalError = '';
    this.form = { MF: '', company: '', first_name: '', last_name: '', date_participation: '' };
  }

  // ── Edit ───────────────────────────────────────────────────────────────────
  openEdit(client: any) {
    this.modalMode  = 'edit';
    this.modalType  = client.type.toLowerCase() as 'b2b' | 'b2c';
    this.editId     = client.id;
    this.modalError = '';
    this.form = {
      MF:                 client.MF || '',
      company:            client.company || '',
      first_name:         client.first_name || '',
      last_name:          client.last_name || '',
      date_participation: client.date_participation || ''
    };
  }

  closeModal() { this.modalMode = null; }

  save() {
    this.saving     = true;
    this.modalError = '';

    const payload: any = {
      type:               this.modalType,
      date_participation: this.form.date_participation || null
    };

    if (this.modalType === 'b2b') {
      payload.MF      = this.form.MF;
      payload.company = this.form.company;
    } else {
      payload.first_name = this.form.first_name;
      payload.last_name  = this.form.last_name;
    }

    const obs = this.modalMode === 'create'
      ? this.api.createClient(payload)
      : this.api.updateClient(this.modalType, this.editId, payload);

    obs.subscribe({
      next: (res) => {
        this.saving    = false;
        this.modalMode = null;
        this.success   = res.message || 'Saved successfully';
        this.load();
        setTimeout(() => this.success = '', 3000);
      },
      error: (err) => {
        this.saving     = false;
        this.modalError = err.error?.error || 'Save failed';
      }
    });
  }

  // ── Delete ─────────────────────────────────────────────────────────────────
  confirmDelete(client: any) { this.deleteTarget = client; }
  cancelDelete()             { this.deleteTarget = null; }

  doDelete() {
    if (!this.deleteTarget) return;
    this.deleting = true;
    this.api.deleteClient(this.deleteTarget.type.toLowerCase(), this.deleteTarget.id).subscribe({
      next: (res) => {
        this.deleting     = false;
        this.deleteTarget = null;
        this.success      = res.message || 'Client deleted';
        this.load();
        setTimeout(() => this.success = '', 3000);
      },
      error: (err) => {
        this.deleting     = false;
        this.error        = err.error?.error || 'Delete failed';
        this.deleteTarget = null;
      }
    });
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  clientName(c: any): string {
    return c.type === 'B2B' ? c.company : c.full_name;
  }

  get b2bCount() { return this.clients.filter(c => c.type === 'B2B').length; }
  get b2cCount() { return this.clients.filter(c => c.type === 'B2C').length; }
}
