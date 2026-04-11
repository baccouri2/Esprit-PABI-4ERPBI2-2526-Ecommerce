import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';

@Component({
  selector: 'app-anomaly',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent],
  templateUrl: './anomaly.component.html',
  styleUrls: ['./anomaly.component.scss']
})
export class AnomalyComponent {
  loading = false;
  error = '';
  advice: Advice | null = null;

  selectedModel = 'isolation_forest';
  sensitivity = 0.05;

  transactions: any[] = [];
  anomalies: any[] = [];
  totalCount = 0;
  anomalyCount = 0;

  models = [
    { value: 'isolation_forest', label: 'Smart Detection' },
    { value: 'one_class_svm',    label: 'Pattern Analysis' },
    { value: 'lof',              label: 'Neighborhood Analysis' }
  ];

  constructor(private http: HttpClient) {}

  detectAnomalies() {
    this.loading = true;
    this.error = '';
    this.http.get<any>('/api/anomaly/detect', {
      params: { model: this.selectedModel, contamination: this.sensitivity.toString() }
    }).subscribe({
      next: (res) => {
        this.transactions  = res.data || [];
        this.anomalies     = this.transactions.filter(t => t.is_anomaly);
        this.totalCount    = res.total || 0;
        this.anomalyCount  = res.anomalies || 0;
        this.loading = false;
        this.buildAdvice();
      },
      error: (err) => {
        this.error = err.error?.error || 'Detection failed';
        this.loading = false;
      }
    });
  }

  getAnomalyRate(): number {
    return this.totalCount > 0 ? (this.anomalyCount / this.totalCount) * 100 : 0;
  }

  private buildAdvice() {
    const rate = this.getAnomalyRate();
    if (rate === 0) {
      this.advice = {
        type: 'success',
        title: 'No Suspicious Transactions Found',
        message: 'All scanned transactions appear normal. Your transaction data looks clean with no irregularities detected.',
        actions: [
          'Schedule regular scans to maintain data integrity',
          'Try a higher sensitivity setting to catch subtle patterns',
          'Keep monitoring as new transactions come in'
        ]
      };
    } else if (rate <= 5) {
      this.advice = {
        type: 'warning',
        title: `${this.anomalyCount} Suspicious Transactions Detected`,
        message: `${rate.toFixed(1)}% of transactions were flagged. This is within a manageable range but warrants a manual review of the highlighted records.`,
        actions: [
          'Review each flagged transaction individually',
          'Check for unusually high discounts or quantities',
          'Verify the flagged transactions with your finance team'
        ]
      };
    } else {
      this.advice = {
        type: 'danger',
        title: `High Anomaly Rate: ${rate.toFixed(1)}%`,
        message: `${this.anomalyCount} out of ${this.totalCount} transactions are suspicious. This is an unusually high rate that requires immediate investigation.`,
        actions: [
          'Immediately escalate to your finance or audit team',
          'Freeze processing on the most suspicious transactions',
          'Lower the sensitivity setting and re-scan to confirm results',
          'Check for system errors or data entry issues'
        ]
      };
    }
  }
}
