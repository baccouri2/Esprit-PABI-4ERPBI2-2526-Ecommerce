import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';
import { TranslationService } from '../../services/translation.service';


interface Lead {
  id: number;
  name: string;
  expected_revenue: number;
  probability: number;
  stage_id: [number, string] | false;
  partner_id: [number, string] | false;
  user_id: [number, string] | false;
  email_from?: string;
  phone?: string;
  description?: string;
  date_deadline?: string;
}

interface LeadFormData {
  id?: number;
  name?: string;
  expected_revenue?: number;
  probability?: number;
  stage_id?: number;
  partner_id?: number;
  user_id?: number;
  email_from?: string;
  phone?: string;
  description?: string;
  date_deadline?: string;
}

interface StageGroup {
  name: string;
  leads: Lead[];
  totalRevenue: number;
  count: number;
}

interface Partner {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  street?: string;
  city?: string;
  zip?: string;
}

interface Stage {
  id: number;
  name: string;
}

interface User {
  id: number;
  name: string;
  email?: string;
}

@Component({
  selector: 'app-crm',
  imports: [CommonModule, FormsModule, SdgFooterComponent],
  templateUrl: './crm.component.html',
  styleUrl: './crm.component.css'
})
export class CrmComponent implements OnInit {
  // Expose Array to template
  Array = Array;

  isLoading = true;
  error = '';
  leads: Lead[] = [];
  stageGroups: StageGroup[] = [];
  totalRevenue = 0;
  totalLeads = 0;

  // Modal states
  showLeadModal = false;
  showPartnerModal = false;
  showDeleteConfirm = false;
  isEditMode = false;
  
  // Form data
  currentLead: LeadFormData = {};
  currentPartner: Partial<Partner> = {};
  leadToDelete: Lead | null = null;
  
  // Dropdown data
  partners: Partner[] = [];
  stages: Stage[] = [];
  users: User[] = [];

  // Configuration Odoo
  private readonly ODOO_LOCAL_URL = 'http://localhost:8069/web#menu_id=139&action=216&model=crm.lead&view_type=kanban';
  private readonly ODOO_EXTERNAL_URL = 'https://esprit10.odoo.com/odoo/crm/1';
  private readonly API_URL = 'http://localhost:5000/api/crm';

  constructor(
    private http: HttpClient,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.loadLeads();
    this.loadPartners();
    this.loadStages();
    this.loadUsers();
  }

  /**
   * Load opportunities from Flask API
   */
  loadLeads() {
    this.isLoading = true;
    this.error = '';

    this.http.get<any>(`${this.API_URL}/leads`).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.leads = response.data;
          this.totalLeads = this.leads.length;
          this.groupLeadsByStage();
          this.calculateTotalRevenue();
          this.isLoading = false;
          console.log('✅ Opportunities loaded:', this.totalLeads);
        } else {
          this.error = 'No opportunities found';
          this.isLoading = false;
        }
      },
      error: (err) => {
        console.error('❌ Error loading opportunities:', err);
        this.error = 'Unable to load opportunities. Make sure backend and Odoo are running.';
        this.isLoading = false;
      }
    });
  }

  /**
   * Load partners (customers)
   */
  loadPartners() {
    this.http.get<any>(`${this.API_URL}/partners?type=customer`).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.partners = response.data;
          console.log('✅ Partners loaded:', this.partners.length);
        }
      },
      error: (err) => {
        console.error('❌ Error loading partners:', err);
      }
    });
  }

  /**
   * Load stages
   */
  loadStages() {
    this.http.get<any>(`${this.API_URL}/stages`).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.stages = response.data;
          console.log('✅ Stages loaded:', this.stages.length);
        }
      },
      error: (err) => {
        console.error('❌ Error loading stages:', err);
      }
    });
  }

  /**
   * Load users (salespeople)
   */
  loadUsers() {
    this.http.get<any>(`${this.API_URL}/users`).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.users = response.data;
          console.log('✅ Users loaded:', this.users.length);
        }
      },
      error: (err) => {
        console.error('❌ Error loading users:', err);
      }
    });
  }

  /**
   * Group opportunities by stage
   */
  groupLeadsByStage() {
    const stageMap = new Map<string, Lead[]>();

    this.leads.forEach(lead => {
      let stageName = 'No stage';
      if (lead.stage_id && Array.isArray(lead.stage_id)) {
        stageName = lead.stage_id[1];
      }
      if (!stageMap.has(stageName)) {
        stageMap.set(stageName, []);
      }
      stageMap.get(stageName)!.push(lead);
    });

    this.stageGroups = Array.from(stageMap.entries()).map(([name, leads]) => ({
      name,
      leads,
      count: leads.length,
      totalRevenue: leads.reduce((sum, lead) => sum + (lead.expected_revenue || 0), 0)
    }));

    // Sort by pipeline order
    const stageOrder = ['New', 'Qualified', 'Proposal', 'Won', 'Lost'];
    this.stageGroups.sort((a, b) => {
      const indexA = stageOrder.indexOf(a.name);
      const indexB = stageOrder.indexOf(b.name);
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });
  }

  /**
   * Calculer le revenu total attendu
   */
  calculateTotalRevenue() {
    this.totalRevenue = this.leads.reduce((sum, lead) => {
      return sum + (lead.expected_revenue || 0);
    }, 0);
  }

  // ============================================================================
  // GESTION DES OPPORTUNITÉS
  // ============================================================================

  /**
   * Open modal to create new opportunity
   */
  openCreateLeadModal() {
    this.isEditMode = false;
    this.currentLead = {
      name: '',
      expected_revenue: 0,
      probability: 50,
      email_from: '',
      phone: '',
      description: ''
    };
    this.showLeadModal = true;
  }

  /**
   * Open modal to edit opportunity
   */
  openEditLeadModal(lead: Lead) {
    this.isEditMode = true;
    this.currentLead = {
      id: lead.id,
      name: lead.name,
      expected_revenue: lead.expected_revenue,
      probability: lead.probability,
      partner_id: lead.partner_id && Array.isArray(lead.partner_id) ? lead.partner_id[0] : undefined,
      stage_id: lead.stage_id && Array.isArray(lead.stage_id) ? lead.stage_id[0] : undefined,
      user_id: lead.user_id && Array.isArray(lead.user_id) ? lead.user_id[0] : undefined,
      email_from: lead.email_from,
      phone: lead.phone,
      description: lead.description,
      date_deadline: lead.date_deadline
    };
    this.showLeadModal = true;
  }

  /**
   * Save opportunity (create or edit)
   */
  saveLead() {
    if (!this.currentLead.name) {
      alert(this.translate.translate('crm.opportunityName') + ' ' + this.translate.translate('common.error').toLowerCase());
      return;
    }

    const leadData: any = {
      name: this.currentLead.name,
      expected_revenue: this.currentLead.expected_revenue || 0,
      probability: this.currentLead.probability || 50,
      email_from: this.currentLead.email_from,
      phone: this.currentLead.phone,
      description: this.currentLead.description,
      date_deadline: this.currentLead.date_deadline
    };

    // Add IDs if defined
    if (this.currentLead.partner_id) {
      leadData.partner_id = this.currentLead.partner_id;
    }
    if (this.currentLead.stage_id) {
      leadData.stage_id = this.currentLead.stage_id;
    }
    if (this.currentLead.user_id) {
      leadData.user_id = this.currentLead.user_id;
    }

    if (this.isEditMode && this.currentLead.id) {
      // Edit
      this.http.put<any>(`${this.API_URL}/leads/${this.currentLead.id}`, leadData).subscribe({
        next: (response) => {
          if (response.success) {
            console.log('✅ Opportunity updated');
            this.closeLeadModal();
            this.loadLeads();
          }
        },
        error: (err) => {
          console.error('❌ Error updating opportunity:', err);
          alert('Error updating opportunity');
        }
      });
    } else {
      // Create
      this.http.post<any>(`${this.API_URL}/leads`, leadData).subscribe({
        next: (response) => {
          if (response.success) {
            console.log('✅ Opportunity created');
            this.closeLeadModal();
            this.loadLeads();
          }
        },
        error: (err) => {
          console.error('❌ Error creating opportunity:', err);
          alert('Error creating opportunity');
        }
      });
    }
  }

  /**
   * Confirm deletion of opportunity
   */
  confirmDeleteLead(lead: Lead) {
    this.leadToDelete = lead;
    this.showDeleteConfirm = true;
  }

  /**
   * Delete opportunity
   */
  deleteLead() {
    if (!this.leadToDelete) return;

    this.http.delete<any>(`${this.API_URL}/leads/${this.leadToDelete.id}`).subscribe({
      next: (response) => {
        if (response.success) {
          console.log('✅ Opportunity deleted');
          this.closeDeleteConfirm();
          this.loadLeads();
        }
      },
      error: (err) => {
        console.error('❌ Error deleting opportunity:', err);
        alert('Error deleting opportunity');
      }
    });
  }

  /**
   * Close opportunity modal
   */
  closeLeadModal() {
    this.showLeadModal = false;
    this.currentLead = {};
  }

  /**
   * Close delete confirmation modal
   */
  closeDeleteConfirm() {
    this.showDeleteConfirm = false;
    this.leadToDelete = null;
  }

  // ============================================================================
  // CUSTOMER MANAGEMENT
  // ============================================================================

  /**
   * Open modal to create new customer
   */
  openCreatePartnerModal() {
    this.currentPartner = {
      name: '',
      email: '',
      phone: '',
      mobile: '',
      street: '',
      city: '',
      zip: ''
    };
    this.showPartnerModal = true;
  }

  /**
   * Save customer
   */
  savePartner() {
    if (!this.currentPartner.name) {
      alert(this.translate.translate('crm.customerName') + ' ' + this.translate.translate('common.error').toLowerCase());
      return;
    }

    const partnerData = {
      name: this.currentPartner.name,
      email: this.currentPartner.email,
      phone: this.currentPartner.phone,
      mobile: this.currentPartner.mobile,
      street: this.currentPartner.street,
      city: this.currentPartner.city,
      zip: this.currentPartner.zip,
      customer_rank: 1
    };

    this.http.post<any>(`${this.API_URL}/partners`, partnerData).subscribe({
      next: (response) => {
        if (response.success) {
          console.log('✅ Customer created');
          this.closePartnerModal();
          this.loadPartners();
        }
      },
      error: (err) => {
        console.error('❌ Error creating customer:', err);
        alert('Error creating customer');
      }
    });
  }

  /**
   * Close customer modal
   */
  closePartnerModal() {
    this.showPartnerModal = false;
    this.currentPartner = {};
  }

  // ============================================================================
  // OTHER METHODS
  // ============================================================================

  /**
   * Open Odoo local in new tab
   */
  openOdooLocal() {
    window.open(this.ODOO_LOCAL_URL, '_blank');
  }

  /**
   * Open external Odoo in new tab
   */
  openOdooExternal() {
    window.open(this.ODOO_EXTERNAL_URL, '_blank');
  }

  /**
   * Refresh data
   */
  refresh() {
    this.loadLeads();
    this.loadPartners();
  }

  /**
   * Get stage color
   */
  getStageColor(stageName: string): string {
    const colors: { [key: string]: string } = {
      'New': '#3b82f6',
      'Qualified': '#8b5cf6',
      'Proposal': '#f59e0b',
      'Won': '#10b981',
      'Lost': '#ef4444'
    };
    return colors[stageName] || '#6b7280';
  }

  /**
   * Format amount as currency
   */
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('fr-TN', {
      style: 'currency',
      currency: 'TND',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  }
}
