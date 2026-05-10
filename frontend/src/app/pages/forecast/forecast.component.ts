import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';

@Component({
  selector: 'app-forecast',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent],
  templateUrl: './forecast.component.html',
  styleUrls: ['./forecast.component.scss']
})
export class ForecastComponent implements OnInit {
  loading = false;
  error = '';
  advice: Advice | null = null;

  selectedModel = 'xgboost';
  weeksAhead = 4;

  historicalData: any[] = [];
  forecastData: any[] = [];

  models = [
    { value: 'xgboost', label: 'AI-Powered Forecast' },
    { value: 'arima', label: 'Trend-Based Forecast' },
    { value: 'sarima', label: 'Seasonal Forecast' },
    { value: 'exp_smoothing', label: 'Smoothed Projection' }
  ];

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  ngOnInit() { this.loadHistoricalData(); }

  loadHistoricalData() {
    this.api.getForecastData().subscribe({
      next: (res) => { this.historicalData = res.data || []; },
      error: () => { this.error = 'Unable to load historical data'; }
    });
  }

  runForecast() {
    // Input validation
    if (this.weeksAhead < 1 || this.weeksAhead > 52) {
      this.error = 'Weeks ahead must be between 1 and 52';
      return;
    }
    this.loading = true;
    this.error = '';
    this.api.predictForecast(this.selectedModel, this.weeksAhead).subscribe({
      next: (res) => {
        this.forecastData = res.forecast || [];
        this.loading = false;
        this.buildAdvice();
      },
      error: (err) => {
        this.error = err.error?.error || 'Forecast failed';
        this.loading = false;
      }
    });
  }

  private buildAdvice() {
    if (!this.forecastData.length) return;
    const quantities = this.forecastData.map(d => d.quantity);
    const avg = quantities.reduce((a, b) => a + b, 0) / quantities.length;
    const max = Math.max(...quantities);
    const min = Math.min(...quantities);
    const trend = quantities[quantities.length - 1] > quantities[0] ? 'up' : 'down';
    const variance = ((max - min) / avg) * 100;

    if (trend === 'up' && variance < 20) {
      this.advice = {
        type: 'success',
        title: 'Steady Growth Detected',
        message: `Sales are projected to grow consistently over the next ${this.weeksAhead} weeks with low volatility (${variance.toFixed(0)}% variance). This is a stable period to invest in stock and marketing.`,
        actions: [
          'Increase inventory levels to meet rising demand',
          'Plan promotional campaigns for peak weeks',
          'Negotiate better supplier terms while demand is predictable'
        ]
      };
    } else if (trend === 'up' && variance >= 20) {
      this.advice = {
        type: 'warning',
        title: 'Growth with High Volatility',
        message: `Sales are trending upward but with significant fluctuations (${variance.toFixed(0)}% variance). Prepare for both high and low demand weeks.`,
        actions: [
          'Maintain flexible stock levels — avoid over-ordering',
          'Set up reorder alerts for fast-moving products',
          'Monitor weekly performance closely'
        ]
      };
    } else if (trend === 'down' && variance < 20) {
      this.advice = {
        type: 'danger',
        title: 'Declining Sales Trend',
        message: `Sales are expected to decline steadily over the next ${this.weeksAhead} weeks. Immediate action is recommended to reverse this trend.`,
        actions: [
          'Launch a targeted discount or promotion campaign',
          'Review product pricing against competitors',
          'Identify and focus on your best-performing products'
        ]
      };
    } else {
      this.advice = {
        type: 'info',
        title: 'Mixed Sales Outlook',
        message: `The forecast shows a mixed pattern over ${this.weeksAhead} weeks. Average expected sales: ${avg.toFixed(0)} units/week. Plan resources accordingly.`,
        actions: [
          'Focus marketing efforts on the highest-forecast weeks',
          'Keep stock levels moderate to reduce holding costs',
          'Re-run the forecast with a longer horizon for better clarity'
        ]
      };
    }
  }
}
