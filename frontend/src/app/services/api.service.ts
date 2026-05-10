import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { timeout, catchError } from 'rxjs/operators';

const API_TIMEOUT = 60000;

@Injectable({ providedIn: 'root' })
export class ApiService {

  constructor(private http: HttpClient) {}

  private get<T>(path: string, params?: Record<string, string>): Observable<T> {
    let httpParams = new HttpParams();
    if (params) Object.entries(params).forEach(([k, v]) => httpParams = httpParams.set(k, v));
    return this.http.get<T>(path, { params: httpParams }).pipe(
      timeout(API_TIMEOUT),
      catchError(err => throwError(() => err))
    );
  }

  private post<T>(path: string, body: unknown): Observable<T> {
    return this.http.post<T>(path, body).pipe(
      timeout(API_TIMEOUT),
      catchError(err => throwError(() => err))
    );
  }

  // ── Dashboard Data ──────────────────────────────────────────────────────────
  getDashboardData() {
    return this.get<any>('/api/data');
  }

  // ── Forecast ────────────────────────────────────────────────────────────────
  getForecastData() {
    return this.get<any>('/api/forecast/data');
  }
  predictForecast(model: string, steps: number) {
    return this.post<any>('/api/forecast/predict', { model, steps });
  }

  // ── Segmentation ────────────────────────────────────────────────────────────
  getSegmentationRfm(clusters: number) {
    return this.get<any>('/api/segmentation/rfm', { clusters: clusters.toString() });
  }
  getSegmentationStats() {
    return this.get<any>('/api/segmentation/stats');
  }

  // ── Anomaly ─────────────────────────────────────────────────────────────────
  detectAnomalies(model: string, contamination: number) {
    return this.get<any>('/api/anomaly/detect', {
      model,
      contamination: contamination.toString()
    });
  }

  // ── Promotion ───────────────────────────────────────────────────────────────
  predictPromotion(payload: {
    model: string;
    unit_price: number;
    discount_rate: number;
    day: number;
    month: number;
    is_weekend: number;
  }) {
    return this.post<any>('/api/promotion/predict', payload);
  }

  // ── Recommendations ─────────────────────────────────────────────────────────
  getClients() {
    return this.get<any>('/api/recommendations/clients');
  }
  getProductRecommendations(client_id: number, top_n: number) {
    return this.post<any>('/api/recommendations/products', { client_id, top_n });
  }

  // ── Sentiment ───────────────────────────────────────────────────────────────
  trainSentiment() {
    return this.get<any>('/api/sentiment/train');
  }
  analyzeSentiment(text: string) {
    return this.post<any>('/api/sentiment/analyze', { text });
  }
  analyzeSentimentBatch() {
    return this.get<any>('/api/sentiment/batch');
  }

  // ── Competition ─────────────────────────────────────────────────────────────
  getCompetitionRecommendations(top_n: number) {
    return this.get<any>('/api/competition/recommendations', { top_n: top_n.toString() });
  }
  getCompetitionCategories() {
    return this.get<any>('/api/competition/categories');
  }
  getCategoryPrice(category: string) {
    return this.get<any>('/api/competition/category-price', { category });
  }

  // ── Chatbot ─────────────────────────────────────────────────────────────────
  chatbotAsk(question: string) {
    return this.post<any>('/api/chatbot/ask', { question });
  }
  chatbotSummarize() {
    return this.get<any>('/api/chatbot/summarize');
  }
  chatbotUpload(formData: FormData) {
    return this.http.post<any>('/api/chatbot/upload', formData).pipe(
      timeout(API_TIMEOUT),
      catchError(err => throwError(() => err))
    );
  }

  // ── Product Management (CRUD) ──────────────────────────────────────────────
  getProductCategories() {
    return this.get<any>('/api/products/categories');
  }
  getAllProducts(q: string = '', category: string = '') {
    const params: Record<string, string> = {};
    if (q) params['q'] = q;
    if (category) params['category'] = category;
    return this.get<any>('/api/products', params);
  }
  getProduct(id: number) {
    return this.get<any>(`/api/products/${id}`);
  }
  createProduct(data: any) {
    return this.post<any>('/api/products', data);
  }
  updateProduct(id: number, data: any) {
    return this.http.put<any>(`/api/products/${id}`, data).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }
  deleteProduct(id: number) {
    return this.http.delete<any>(`/api/products/${id}`).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }

  // ── Supplier Management (CRUD) ─────────────────────────────────────────────
  getAllSuppliers(q: string = '') {
    return this.get<any>('/api/suppliers', q ? { q } : {});
  }
  getSupplier(id: number) {
    return this.get<any>(`/api/suppliers/${id}`);
  }
  createSupplier(data: any) {
    return this.post<any>('/api/suppliers', data);
  }
  updateSupplier(id: number, data: any) {
    return this.http.put<any>(`/api/suppliers/${id}`, data).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }
  deleteSupplier(id: number) {
    return this.http.delete<any>(`/api/suppliers/${id}`).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }

  // ── Client Management (CRUD) ────────────────────────────────────────────────
  getAllClients(type: 'all' | 'b2b' | 'b2c' = 'all') {
    return this.get<any>('/api/clients', { type });
  }
  getClient(clientType: string, id: number) {
    return this.get<any>(`/api/clients/${clientType}/${id}`);
  }
  createClient(data: any) {
    return this.post<any>('/api/clients', data);
  }
  updateClient(clientType: string, id: number, data: any) {
    return this.http.put<any>(`/api/clients/${clientType}/${id}`, data).pipe(
      timeout(API_TIMEOUT),
      catchError(err => throwError(() => err))
    );
  }
  deleteClient(clientType: string, id: number) {
    return this.http.delete<any>(`/api/clients/${clientType}/${id}`).pipe(
      timeout(API_TIMEOUT),
      catchError(err => throwError(() => err))
    );
  }
  searchClients(q: string, type: string = 'all') {
    return this.get<any>('/api/clients/search', { q, type });
  }

  // ── Order Management (CRUD) ─────────────────────────────────────────────────
  getAllOrders(q: string = '', status: string = '') {
    const params: Record<string, string> = {};
    if (q) params['q'] = q;
    if (status) params['status'] = status;
    return this.get<any>('/api/orders', params);
  }
  getOrder(id: number) {
    return this.get<any>(`/api/orders/${id}`);
  }
  createOrder(data: any) {
    return this.post<any>('/api/orders', data);
  }
  updateOrder(id: number, data: any) {
    return this.http.put<any>(`/api/orders/${id}`, data).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }
  deleteOrder(id: number) {
    return this.http.delete<any>(`/api/orders/${id}`).pipe(
      timeout(API_TIMEOUT), catchError(err => throwError(() => err))
    );
  }
  getOrderStatuses() {
    return this.get<any>('/api/orders/statuses');
  }
  downloadInvoice(id: number) {
    return this.http.get(`/api/orders/${id}/invoice`, {
      responseType: 'blob'
    });
  }
}
