import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';

type ModalMode = 'create' | 'edit' | null;

@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './products.component.html',
  styleUrls: ['./products.component.scss']
})
export class ProductsComponent implements OnInit {
  products:   any[] = [];
  categories: any[] = [];
  loading     = false;
  error       = '';
  success     = '';

  searchQ          = '';
  filterCategory   = '';

  modalMode:  ModalMode = null;
  saving      = false;
  modalError  = '';
  editId      = 0;

  form = { name_product: '', ref_product: '', fk_category: 0 };

  deleteTarget: any = null;
  deleting     = false;

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.loadCategories();
    this.load();
  }

  loadCategories() {
    this.api.getProductCategories().subscribe({
      next: (res: any) => { this.categories = res.categories || []; }
    });
  }

  load() {
    this.loading = true;
    this.error   = '';
    this.api.getAllProducts(this.searchQ, this.filterCategory).subscribe({
      next: (res: any) => { this.products = res.products || []; this.loading = false; },
      error: (err: any) => { this.error = err.error?.error || 'Failed to load products'; this.loading = false; }
    });
  }

  onSearch()   { this.load(); }
  onFilter()   { this.load(); }
  clearFilter(){ this.filterCategory = ''; this.load(); }

  openCreate() {
    this.modalMode  = 'create';
    this.modalError = '';
    this.form = { name_product: '', ref_product: '', fk_category: this.categories[0]?.id || 0 };
  }

  openEdit(p: any) {
    this.modalMode  = 'edit';
    this.editId     = p.id;
    this.modalError = '';
    this.form = {
      name_product: p.name_product,
      ref_product:  p.ref_product,
      fk_category:  p.fk_category
    };
  }

  closeModal() { this.modalMode = null; }

  save() {
    if (!this.form.name_product.trim()) { this.modalError = 'Product name is required'; return; }
    if (!this.form.ref_product.trim())  { this.modalError = 'Reference is required'; return; }
    if (!this.form.fk_category)         { this.modalError = 'Category is required'; return; }

    this.saving     = true;
    this.modalError = '';

    const obs = this.modalMode === 'create'
      ? this.api.createProduct(this.form)
      : this.api.updateProduct(this.editId, this.form);

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

  confirmDelete(p: any) { this.deleteTarget = p; }
  cancelDelete()        { this.deleteTarget = null; }

  doDelete() {
    if (!this.deleteTarget) return;
    this.deleting = true;
    this.api.deleteProduct(this.deleteTarget.id).subscribe({
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

  getCategoryName(id: number): string {
    return this.categories.find(c => c.id === id)?.name || 'Unknown';
  }

  get uniqueCategories(): string[] {
    return [...new Set(this.products.map(p => p.name_category))].sort();
  }

  get withSales(): number {
    return this.products.filter(p => p.sale_count > 0).length;
  }
}
