import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';

@Component({
  selector: 'app-promotion',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent, SdgFooterComponent],
  templateUrl: './promotion.component.html',
  styleUrls: ['./promotion.component.scss']
})
export class PromotionComponent {
  loading = false;
  error = '';
  advice: Advice | null = null;

  selectedModel = 'random_forest';
  unitPrice = 50;
  discountRate = 0.1;
  day = 15;
  month = 6;
  isWeekend = 0;

  result: any = null;

  models = [
    { value: 'random_forest',     label: 'AI-Powered Prediction' },
    { value: 'gradient_boosting', label: 'Boosted Prediction' },
    { value: 'linear_regression', label: 'Trend Projection' }
  ];

  months = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  predictImpact() {
    // Input validation
    if (this.unitPrice <= 0) { this.error = 'Unit price must be greater than 0'; return; }
    if (this.discountRate < 0 || this.discountRate > 0.99) { this.error = 'Discount rate must be between 0 and 0.99'; return; }
    if (this.day < 1 || this.day > 31) { this.error = 'Day must be between 1 and 31'; return; }
    if (this.month < 1 || this.month > 12) { this.error = 'Month must be between 1 and 12'; return; }
    this.loading = true;
    this.error = '';
    this.api.predictPromotion({
      model: this.selectedModel,
      unit_price: this.unitPrice,
      discount_rate: this.discountRate,
      day: this.day,
      month: this.month,
      is_weekend: this.isWeekend
    }).subscribe({
      next: (res) => {
        this.result = res;
        this.loading = false;
        this.buildAdvice();
      },
      error: (err) => {
        this.error = err.error?.error || 'Prediction failed';
        this.loading = false;
      }
    });
  }

  getDiscountPercent(): number { return this.discountRate * 100; }

  private buildAdvice() {
    if (!this.result) return;
    const qty      = this.result.predicted_quantity;
    const revenue  = qty * this.unitPrice * (1 - this.discountRate);
    const r2       = (this.result.metrics?.r2 || 0) * 100;
    const discount = this.getDiscountPercent();

    if (r2 >= 75 && discount <= 20) {
      this.advice = {
        type: 'success',
        title: 'High-Confidence Campaign',
        message: `This campaign is predicted to sell ${qty.toFixed(0)} units and generate ${revenue.toFixed(0)} DT in revenue with ${r2.toFixed(0)}% confidence. The discount level is sustainable.`,
        actions: [
          'Proceed with this campaign — the numbers look strong',
          'Prepare stock for the predicted demand',
          `Consider running this campaign on ${this.isWeekend ? 'weekends' : 'weekdays'} as configured`
        ]
      };
    } else if (discount > 30) {
      this.advice = {
        type: 'warning',
        title: 'High Discount — Check Profitability',
        message: `A ${discount.toFixed(0)}% discount may erode your margins. While ${qty.toFixed(0)} units are predicted, verify that the estimated revenue of ${revenue.toFixed(0)} DT covers your costs.`,
        actions: [
          'Calculate your break-even point before launching',
          'Consider reducing the discount to 15–20% for better margins',
          'Test with a smaller product batch first'
        ]
      };
    } else if (r2 < 50) {
      this.advice = {
        type: 'info',
        title: 'Low Confidence — Proceed with Caution',
        message: `The prediction confidence is ${r2.toFixed(0)}%, which is relatively low. The ${qty.toFixed(0)} unit estimate may vary significantly in practice.`,
        actions: [
          'Run a small pilot campaign before full rollout',
          'Try a different prediction method for comparison',
          'Collect more historical data to improve accuracy'
        ]
      };
    } else {
      this.advice = {
        type: 'info',
        title: 'Campaign Looks Viable',
        message: `Expected to sell ${qty.toFixed(0)} units and generate ${revenue.toFixed(0)} DT. Confidence level is ${r2.toFixed(0)}%.`,
        actions: [
          'Align your inventory with the predicted demand',
          'Schedule the campaign for the selected period',
          'Track actual vs predicted results after launch'
        ]
      };
    }
  }
}
