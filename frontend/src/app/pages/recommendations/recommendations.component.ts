import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent],
  templateUrl: './recommendations.component.html',
  styleUrls: ['./recommendations.component.scss']
})
export class RecommendationsComponent implements OnInit {
  loadingClients = false;
  loadingRecs = false;
  error = '';
  advice: Advice | null = null;

  clients: any[] = [];
  selectedClientId: number | null = null;
  topN = 5;
  result: any = null;

  constructor(private http: HttpClient) {}

  ngOnInit() { this.loadClients(); }

  loadClients() {
    this.loadingClients = true;
    this.http.get<any>('/api/recommendations/clients').subscribe({
      next: (res) => {
        this.clients = res.clients || [];
        if (this.clients.length > 0) this.selectedClientId = this.clients[0].client_id;
        this.loadingClients = false;
      },
      error: () => {
        this.error = 'Unable to load customers';
        this.loadingClients = false;
      }
    });
  }

  getRecommendations() {
    if (!this.selectedClientId) return;
    this.loadingRecs = true;
    this.error = '';
    this.result = null;
    this.http.post<any>('/api/recommendations/products', {
      client_id: this.selectedClientId,
      top_n: this.topN
    }).subscribe({
      next: (res) => {
        this.result = res;
        this.loadingRecs = false;
        this.buildAdvice();
      },
      error: (err) => {
        this.error = err.error?.error || 'Could not generate suggestions';
        this.loadingRecs = false;
      }
    });
  }

  getScorePercent(score: number): number {
    if (!this.result?.recommendations?.length) return 0;
    const max = this.result.recommendations[0].score;
    return max > 0 ? (score / max) * 100 : 0;
  }

  private buildAdvice() {
    if (!this.result) return;
    const recs = this.result.recommendations || [];
    const history = this.result.purchase_history || [];
    const topMatch = recs.length > 0 ? this.getScorePercent(recs[0].score) : 0;
    const clientName = this.result.client_name || 'This customer';

    if (recs.length === 0) {
      this.advice = {
        type: 'info',
        title: 'Customer Has Explored Everything',
        message: `${clientName} has already purchased from all available product categories. Focus on new product introductions or exclusive offers.`,
        actions: [
          'Introduce new products to re-engage this customer',
          'Offer a loyalty reward for their continued business',
          'Suggest premium or upgraded versions of past purchases'
        ]
      };
    } else if (topMatch >= 80) {
      this.advice = {
        type: 'success',
        title: 'Strong Product Matches Found',
        message: `${recs.length} highly relevant products identified for ${clientName}. The top recommendation has a ${topMatch.toFixed(0)}% match score — very likely to convert.`,
        actions: [
          `Prioritize "${recs[0].name}" in your next outreach to this customer`,
          'Send a personalized email featuring the top 3 suggestions',
          'Offer a small bundle discount to increase basket size'
        ]
      };
    } else if (history.length < 3) {
      this.advice = {
        type: 'warning',
        title: 'Limited Purchase History',
        message: `${clientName} has only ${history.length} recorded purchase(s). Recommendations may be less accurate with limited data.`,
        actions: [
          'Encourage this customer to explore more product categories',
          'Offer a first-purchase incentive on suggested products',
          'Re-run suggestions after more purchases are recorded'
        ]
      };
    } else {
      this.advice = {
        type: 'info',
        title: `${recs.length} Products Suggested for ${clientName}`,
        message: `Based on ${history.length} past purchases, we found ${recs.length} relevant products. Use these to personalize your next sales interaction.`,
        actions: [
          'Share the top suggestions in your next customer touchpoint',
          'Group suggestions by category for a cleaner presentation',
          'Track which suggestions lead to actual purchases'
        ]
      };
    }
  }
}
