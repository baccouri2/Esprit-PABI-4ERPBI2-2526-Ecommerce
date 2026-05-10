import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';

@Component({
  selector: 'app-recommendations',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent, SdgFooterComponent],
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
      next: (res) => { this.competitionRecommendations = res.recommendations || []; this.competitionLoading = false; },
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

  exportPDF() {
    const html2pdf = (window as any).html2pdf;
    if (!html2pdf) {
      alert('PDF export library not loaded');
      return;
    }

    const element = document.createElement('div');
    element.style.padding = '20px';
    element.style.fontFamily = 'Arial, sans-serif';
    element.style.color = '#000';
    element.style.backgroundColor = '#fff';

    // Logo and Header
    const headerDiv = document.createElement('div');
    headerDiv.style.display = 'flex';
    headerDiv.style.alignItems = 'center';
    headerDiv.style.justifyContent = 'space-between';
    headerDiv.style.marginBottom = '30px';
    headerDiv.style.paddingBottom = '20px';
    headerDiv.style.borderBottom = '2px solid #1a2942';

    // Logo
    const logo = document.createElement('img');
    logo.src = '/sougui_logo.png';
    logo.style.height = '60px';
    logo.style.width = 'auto';
    headerDiv.appendChild(logo);

    // Title
    const titleDiv = document.createElement('div');
    titleDiv.style.flex = '1';
    titleDiv.style.marginLeft = '20px';

    const title = document.createElement('h1');
    title.textContent = 'Smart Suggestions Report';
    title.style.color = '#1a2942';
    title.style.margin = '0 0 5px 0';
    title.style.fontSize = '28px';
    titleDiv.appendChild(title);

    const subtitle = document.createElement('p');
    subtitle.textContent = 'Sougui Analytics Dashboard';
    subtitle.style.color = '#666';
    subtitle.style.margin = '0';
    subtitle.style.fontSize = '12px';
    titleDiv.appendChild(subtitle);

    headerDiv.appendChild(titleDiv);
    element.appendChild(headerDiv);

    // Date
    const date = document.createElement('p');
    date.textContent = `Generated: ${new Date().toLocaleString()}`;
    date.style.color = '#000';
    date.style.marginBottom = '20px';
    date.style.fontSize = '12px';
    element.appendChild(date);

    // Customer Info
    if (this.result) {
      const customerSection = document.createElement('div');
      customerSection.style.marginBottom = '30px';
      customerSection.style.borderBottom = '2px solid #1a2942';
      customerSection.style.paddingBottom = '15px';

      const customerTitle = document.createElement('h2');
      customerTitle.textContent = 'Customer Information';
      customerTitle.style.color = '#1a2942';
      customerTitle.style.fontSize = '18px';
      customerTitle.style.marginBottom = '10px';
      customerSection.appendChild(customerTitle);

      const customerInfo = document.createElement('p');
      customerInfo.innerHTML = `
        <strong>Name:</strong> ${this.result.client_name || 'N/A'}<br>
        <strong>Type:</strong> ${this.result.client_type || 'N/A'}<br>
        <strong>Purchase History:</strong> ${this.result.purchase_history?.length || 0} products
      `;
      customerInfo.style.lineHeight = '1.8';
      customerInfo.style.color = '#000';
      customerSection.appendChild(customerInfo);
      element.appendChild(customerSection);

      // Recommendations
      if (this.result.recommendations && this.result.recommendations.length > 0) {
        const recsSection = document.createElement('div');
        recsSection.style.marginBottom = '30px';
        recsSection.style.borderBottom = '2px solid #1a2942';
        recsSection.style.paddingBottom = '15px';

        const recsTitle = document.createElement('h2');
        recsTitle.textContent = `Recommended Products (${this.result.recommendations.length})`;
        recsTitle.style.color = '#1a2942';
        recsTitle.style.fontSize = '18px';
        recsTitle.style.marginBottom = '10px';
        recsSection.appendChild(recsTitle);

        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.style.marginBottom = '10px';

        // Table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.style.backgroundColor = '#e8eaf6';
        ['Rank', 'Product Name', 'Category', 'Match Score'].forEach(header => {
          const th = document.createElement('th');
          th.textContent = header;
          th.style.border = '1px solid #000';
          th.style.padding = '10px';
          th.style.textAlign = 'left';
          th.style.fontWeight = 'bold';
          th.style.color = '#000';
          headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Table body
        const tbody = document.createElement('tbody');
        this.result.recommendations.forEach((rec: any, index: number) => {
          const row = document.createElement('tr');
          row.style.borderBottom = '1px solid #000';

          const rankCell = document.createElement('td');
          rankCell.textContent = `#${index + 1}`;
          rankCell.style.padding = '10px';
          rankCell.style.border = '1px solid #000';
          rankCell.style.color = '#000';
          row.appendChild(rankCell);

          const nameCell = document.createElement('td');
          nameCell.textContent = rec.name;
          nameCell.style.padding = '10px';
          nameCell.style.border = '1px solid #000';
          nameCell.style.color = '#000';
          row.appendChild(nameCell);

          const categoryCell = document.createElement('td');
          categoryCell.textContent = rec.category;
          categoryCell.style.padding = '10px';
          categoryCell.style.border = '1px solid #000';
          categoryCell.style.color = '#000';
          row.appendChild(categoryCell);

          const scoreCell = document.createElement('td');
          const score = this.getScorePercent(rec.score);
          scoreCell.textContent = `${score.toFixed(0)}%`;
          scoreCell.style.padding = '10px';
          scoreCell.style.border = '1px solid #000';
          scoreCell.style.color = '#000';
          scoreCell.style.fontWeight = 'bold';
          row.appendChild(scoreCell);

          tbody.appendChild(row);
        });
        table.appendChild(tbody);
        recsSection.appendChild(table);
        element.appendChild(recsSection);
      }

      // Purchase History
      if (this.result.purchase_history && this.result.purchase_history.length > 0) {
        const historySection = document.createElement('div');
        historySection.style.marginBottom = '30px';

        const historyTitle = document.createElement('h2');
        historyTitle.textContent = `Purchase History (${this.result.purchase_history.length})`;
        historyTitle.style.color = '#1a2942';
        historyTitle.style.fontSize = '18px';
        historyTitle.style.marginBottom = '10px';
        historySection.appendChild(historyTitle);

        const historyTable = document.createElement('table');
        historyTable.style.width = '100%';
        historyTable.style.borderCollapse = 'collapse';

        // Table header
        const historyThead = document.createElement('thead');
        const historyHeaderRow = document.createElement('tr');
        historyHeaderRow.style.backgroundColor = '#e8eaf6';
        ['Product', 'Category', 'Units Bought'].forEach(header => {
          const th = document.createElement('th');
          th.textContent = header;
          th.style.border = '1px solid #000';
          th.style.padding = '10px';
          th.style.textAlign = 'left';
          th.style.fontWeight = 'bold';
          th.style.color = '#000';
          historyHeaderRow.appendChild(th);
        });
        historyThead.appendChild(historyHeaderRow);
        historyTable.appendChild(historyThead);

        // Table body
        const historyTbody = document.createElement('tbody');
        this.result.purchase_history.forEach((item: any) => {
          const row = document.createElement('tr');
          row.style.borderBottom = '1px solid #000';

          const productCell = document.createElement('td');
          productCell.textContent = item.name_product;
          productCell.style.padding = '10px';
          productCell.style.border = '1px solid #000';
          productCell.style.color = '#000';
          row.appendChild(productCell);

          const categoryCell = document.createElement('td');
          categoryCell.textContent = item.name_category;
          categoryCell.style.padding = '10px';
          categoryCell.style.border = '1px solid #000';
          categoryCell.style.color = '#000';
          row.appendChild(categoryCell);

          const qtyCell = document.createElement('td');
          qtyCell.textContent = `${item.total_qty} units`;
          qtyCell.style.padding = '10px';
          qtyCell.style.border = '1px solid #000';
          qtyCell.style.color = '#000';
          row.appendChild(qtyCell);

          historyTbody.appendChild(row);
        });
        historyTable.appendChild(historyTbody);
        historySection.appendChild(historyTable);
        element.appendChild(historySection);
      }
    }

    // Competition Analysis Summary
    if (this.competitionRecommendations.length > 0) {
      const compSection = document.createElement('div');
      compSection.style.marginBottom = '30px';
      compSection.style.borderBottom = '2px solid #1a2942';
      compSection.style.paddingBottom = '15px';

      const compTitle = document.createElement('h2');
      compTitle.textContent = `Competition Analysis (${this.competitionRecommendations.length} Products)`;
      compTitle.style.color = '#1a2942';
      compTitle.style.fontSize = '18px';
      compTitle.style.marginBottom = '10px';
      compSection.appendChild(compTitle);

      const compTable = document.createElement('table');
      compTable.style.width = '100%';
      compTable.style.borderCollapse = 'collapse';

      // Table header
      const compThead = document.createElement('thead');
      const compHeaderRow = document.createElement('tr');
      compHeaderRow.style.backgroundColor = '#e8eaf6';
      ['Rank', 'Product', 'Category', 'Price', 'Success Probability'].forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        th.style.border = '1px solid #000';
        th.style.padding = '10px';
        th.style.textAlign = 'left';
        th.style.fontWeight = 'bold';
        th.style.color = '#000';
        compHeaderRow.appendChild(th);
      });
      compThead.appendChild(compHeaderRow);
      compTable.appendChild(compThead);

      // Table body
      const compTbody = document.createElement('tbody');
      this.competitionRecommendations.forEach((product: any, index: number) => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #000';

        const rankCell = document.createElement('td');
        rankCell.textContent = `#${index + 1}`;
        rankCell.style.padding = '10px';
        rankCell.style.border = '1px solid #000';
        rankCell.style.color = '#000';
        row.appendChild(rankCell);

        const nameCell = document.createElement('td');
        nameCell.textContent = product.name;
        nameCell.style.padding = '10px';
        nameCell.style.border = '1px solid #000';
        nameCell.style.color = '#000';
        row.appendChild(nameCell);

        const categoryCell = document.createElement('td');
        categoryCell.textContent = product.category;
        categoryCell.style.padding = '10px';
        categoryCell.style.border = '1px solid #000';
        categoryCell.style.color = '#000';
        row.appendChild(categoryCell);

        const priceCell = document.createElement('td');
        priceCell.textContent = `${product.price} DT`;
        priceCell.style.padding = '10px';
        priceCell.style.border = '1px solid #000';
        priceCell.style.color = '#000';
        row.appendChild(priceCell);

        const probCell = document.createElement('td');
        probCell.textContent = `${product.probability}%`;
        probCell.style.padding = '10px';
        probCell.style.border = '1px solid #000';
        probCell.style.color = '#000';
        probCell.style.fontWeight = 'bold';
        row.appendChild(probCell);

        compTbody.appendChild(row);
      });
      compTable.appendChild(compTbody);
      compSection.appendChild(compTable);
      element.appendChild(compSection);
    }

    // Export
    const opt = {
      margin: 10,
      filename: `recommendations-report-${new Date().getTime()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };

    html2pdf().set(opt).from(element).save();
  }
}
