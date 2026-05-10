/**
 * Service Angular pour l'API CRM Odoo
 * Gère les appels HTTP vers Flask qui communique avec Odoo
 */

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface OdooLead {
  id: number;
  name: string;
  partner_id: [number, string] | false;
  expected_revenue: number;
  probability: number;
  stage_id: [number, string] | false;
  user_id: [number, string] | false;
  email_from?: string;
  phone?: string;
  description?: string;
  date_deadline?: string;
  create_date?: string;
}

export interface OdooStage {
  id: number;
  name: string;
  sequence: number;
  fold: boolean;
}

export interface OdooPartner {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  street?: string;
  city?: string;
  zip?: string;
  customer_rank?: number;
  supplier_rank?: number;
}

export interface OdooUser {
  id: number;
  name: string;
  email?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  count?: number;
}

@Injectable({
  providedIn: 'root'
})
export class OdooCrmService {
  private baseUrl = 'http://localhost:5000/api/crm';

  constructor(private http: HttpClient) {}

  // ========================================================================
  // LEADS / OPPORTUNITIES
  // ========================================================================

  /**
   * Récupérer la liste des leads/opportunités
   */
  getLeads(params?: {
    limit?: number;
    offset?: number;
    stage_id?: number;
    user_id?: number;
  }): Observable<ApiResponse<OdooLead[]>> {
    let httpParams = new HttpParams();
    
    if (params) {
      if (params.limit) httpParams = httpParams.set('limit', params.limit.toString());
      if (params.offset) httpParams = httpParams.set('offset', params.offset.toString());
      if (params.stage_id) httpParams = httpParams.set('stage_id', params.stage_id.toString());
      if (params.user_id) httpParams = httpParams.set('user_id', params.user_id.toString());
    }

    return this.http.get<ApiResponse<OdooLead[]>>(`${this.baseUrl}/leads`, { params: httpParams });
  }

  /**
   * Récupérer un lead spécifique
   */
  getLead(id: number): Observable<ApiResponse<OdooLead>> {
    return this.http.get<ApiResponse<OdooLead>>(`${this.baseUrl}/leads/${id}`);
  }

  /**
   * Créer un nouveau lead
   */
  createLead(lead: Partial<OdooLead>): Observable<ApiResponse<{ id: number }>> {
    return this.http.post<ApiResponse<{ id: number }>>(`${this.baseUrl}/leads`, lead);
  }

  /**
   * Mettre à jour un lead
   */
  updateLead(id: number, data: Partial<OdooLead>): Observable<ApiResponse<any>> {
    return this.http.put<ApiResponse<any>>(`${this.baseUrl}/leads/${id}`, data);
  }

  /**
   * Supprimer un lead
   */
  deleteLead(id: number): Observable<ApiResponse<any>> {
    return this.http.delete<ApiResponse<any>>(`${this.baseUrl}/leads/${id}`);
  }

  // ========================================================================
  // STAGES
  // ========================================================================

  /**
   * Récupérer les étapes du pipeline CRM
   */
  getStages(): Observable<ApiResponse<OdooStage[]>> {
    return this.http.get<ApiResponse<OdooStage[]>>(`${this.baseUrl}/stages`);
  }

  // ========================================================================
  // PARTNERS (Clients/Fournisseurs)
  // ========================================================================

  /**
   * Récupérer les partenaires
   */
  getPartners(type?: 'customer' | 'supplier', limit?: number): Observable<ApiResponse<OdooPartner[]>> {
    let params = new HttpParams();
    if (type) params = params.set('type', type);
    if (limit) params = params.set('limit', limit.toString());

    return this.http.get<ApiResponse<OdooPartner[]>>(`${this.baseUrl}/partners`, { params });
  }

  /**
   * Créer un nouveau partenaire
   */
  createPartner(partner: Partial<OdooPartner>): Observable<ApiResponse<{ id: number }>> {
    return this.http.post<ApiResponse<{ id: number }>>(`${this.baseUrl}/partners`, partner);
  }

  // ========================================================================
  // USERS (Vendeurs)
  // ========================================================================

  /**
   * Récupérer les utilisateurs (vendeurs)
   */
  getUsers(): Observable<ApiResponse<OdooUser[]>> {
    return this.http.get<ApiResponse<OdooUser[]>>(`${this.baseUrl}/users`);
  }

  // ========================================================================
  // HEALTH CHECK
  // ========================================================================

  /**
   * Vérifier la connexion à Odoo
   */
  healthCheck(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.baseUrl}/health`);
  }
}
