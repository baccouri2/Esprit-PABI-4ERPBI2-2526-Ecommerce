import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';

@Component({
  selector: 'app-competition',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent, SdgFooterComponent],
  templateUrl: './competition.component.html',
  styleUrls: ['./competition.component.scss']
})
export class CompetitionComponent implements OnInit {
  loadingClients = false;
  loadingRecs = false;
  error = '';
  advice: Advice | null = null;

  // Customer recommendations
  clients: any[] = [];
  selectedClientId: number | null = null;
  topN = 5;
  result: any = null;

  // Competition & International
  competitionTab: 'competition' | 'international' = 'competition';
  competitionRecommendations: any[] = [];
  competitionLoading = false;
  competitionTopN = 10;
  categories: any[] = [];
  selectedCategory = '';
  categoryPrice: any = null;
  categoryLoading = false;

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.loadClients();
    this.loadCompetitionData();
  }

  loadClients() {
    this.loadingClients = true;
    this.api.getClients().subscribe({
      next: (res) => {
        this.clients = res.clients || [];
        if (this.clients.length > 0) this.selectedClientId = this.clients[0].client_id;
        this.loadingClients = false;
      },
      error: () => { this.error = 'Unable to load customers'; this.loadingClients = false; }
    });
  }

  getRecommendations() {
    if (!this.selectedClientId) { this.error = 'Please select a customer'; return; }
    if (this.topN < 1 || this.topN > 20) { this.error = 'Number of suggestions must be between 1 and 20'; return; }
    this.loadingRecs = true;
    this.error = '';
    this.result = null;
    this.api.getProductRecommendations(this.selectedClientId, this.topN).subscribe({
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

  loadCompetitionData() {
    this.api.getCompetitionCategories().subscribe({
      next: (res) => {
        this.categories = res.categories || [];
        if (this.categories.length > 0) this.selectedCategory = this.categories[0].category;
      },
      error: () => { this.categories = []; }
    });
    this.loadCompetitionRecommendations();
  }

  loadCompetitionRecommendations() {
    this.competitionLoading = true;
    this.api.getCompetitionRecommendations(this.competitionTopN).subscribe({
      next: (res) => {
        this.competitionRecommendations = res.recommendations || [];
        this.competitionLoading = false;
        this.buildCompetitionAdvice();
      },
      error: () => { this.competitionRecommendations = []; this.competitionLoading = false; }
    });
  }

  getCategoryPrice() {
    if (!this.selectedCategory) return;
    this.categoryLoading = true;
    this.api.getCategoryPrice(this.selectedCategory).subscribe({
      next: (res) => { this.categoryPrice = res; this.categoryLoading = false; },
      error: () => { this.categoryPrice = null; this.categoryLoading = false; }
    });
  }

  private buildCompetitionAdvice() {
    const recs = this.competitionRecommendations;
    if (!recs.length) return;
    const highProb = recs.filter(r => r.probability >= 80).length;
    const avgProb  = recs.reduce((s: number, r: any) => s + r.probability, 0) / recs.length;
    const topProduct = recs[0];

    if (highProb >= 3) {
      this.advice = {
        type: 'success',
        title: `${highProb} High-Potential Products Identified`,
        message: `The competition analysis found ${highProb} products with over 80% success probability. "${topProduct.name}" leads with ${topProduct.probability}% — strong candidates to add to your catalogue.`,
        actions: [
          `Prioritize stocking "${topProduct.name}" (${topProduct.category}) at ${topProduct.price} DT`,
          'Compare your current prices against these competitor benchmarks',
          'Focus on the top 3 products for your next procurement cycle'
        ]
      };
    } else if (avgProb >= 60) {
      this.advice = {
        type: 'info',
        title: 'Moderate Competition Opportunity',
        message: `Average success probability across ${recs.length} competitor products is ${avgProb.toFixed(0)}%. There are opportunities to capture market share with the right pricing strategy.`,
        actions: [
          'Review the top-ranked products and compare with your current catalogue',
          'Identify categories where competitors are strongest',
          'Consider a pilot with 2–3 of the highest-probability products'
        ]
      };
    } else {
      this.advice = {
        type: 'warning',
        title: 'Low Competitive Differentiation',
        message: `Most competitor products show below 60% success probability (avg: ${avgProb.toFixed(0)}%). The market may be saturated or data is limited.`,
        actions: [
          'Focus on your existing best-sellers rather than copying competitors',
          'Look for niche categories with less competition',
          'Update the competitor data file for more accurate analysis'
        ]
      };
    }
  }

  getProbabilityColor(probability: number): string {
    if (probability >= 80) return '#10b981';
    if (probability >= 60) return '#3b82f6';
    if (probability >= 40) return '#f59e0b';
    return '#ef4444';
  }

  getProbabilityLabel(probability: number): string {
    if (probability >= 80) return 'Very High';
    if (probability >= 60) return 'High';
    if (probability >= 40) return 'Medium';
    return 'Low';
  }

  formatNumber(value: number): string {
    return value.toLocaleString('en-US');
  }
}
