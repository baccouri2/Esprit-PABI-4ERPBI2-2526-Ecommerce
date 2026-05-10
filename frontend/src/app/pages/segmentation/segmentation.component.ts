import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-segmentation',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent],
  templateUrl: './segmentation.component.html',
  styleUrls: ['./segmentation.component.scss']
})
export class SegmentationComponent implements OnInit {
  loading = false;
  error = '';
  advice: Advice | null = null;

  clusters = 3;
  customers: any[] = [];
  stats: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadSegmentation(); }

  loadSegmentation() {
    // Input validation
    if (this.clusters < 2 || this.clusters > 10) {
      this.error = 'Number of clusters must be between 2 and 10';
      return;
    }
    this.loading = true;
    this.error = '';
    Promise.all([
      this.api.getSegmentationRfm(this.clusters).toPromise(),
      this.api.getSegmentationStats().toPromise()
    ]).then(([rfmRes, statsRes]) => {
      this.customers = rfmRes?.data || [];
      this.stats = statsRes?.stats || [];
      this.loading = false;
      this.buildAdvice();
    }).catch(() => {
      this.error = 'Unable to load customer data';
      this.loading = false;
    });
  }

  getSegmentClass(segment: string): string {
    if (segment.includes('High')) return 'badge-success';
    if (segment.includes('Mid')) return 'badge-info';
    return 'badge-warning';
  }

  private buildAdvice() {
    if (!this.customers.length) return;
    const high = this.customers.filter(c => c.segment?.includes('High')).length;
    const low  = this.customers.filter(c => c.segment?.includes('Low')).length;
    const total = this.customers.length;
    const highPct = Math.round((high / total) * 100);
    const lowPct  = Math.round((low  / total) * 100);

    if (highPct >= 30) {
      this.advice = {
        type: 'success',
        title: 'Strong Customer Base',
        message: `${highPct}% of your customers are high-value. This is an excellent foundation for growth. Focus on retaining them and converting mid-value customers.`,
        actions: [
          'Launch a loyalty program for your top customers',
          'Offer exclusive early access to new products',
          `Target the ${lowPct}% low-value segment with re-engagement campaigns`
        ]
      };
    } else if (lowPct >= 50) {
      this.advice = {
        type: 'danger',
        title: 'High Proportion of Inactive Customers',
        message: `${lowPct}% of your customers are low-value or inactive. This signals a retention problem that needs immediate attention.`,
        actions: [
          'Send win-back emails with special discount offers',
          'Identify why customers stopped purchasing',
          'Focus acquisition efforts on higher-quality leads'
        ]
      };
    } else {
      this.advice = {
        type: 'info',
        title: 'Balanced Customer Distribution',
        message: `Your customer base is fairly balanced across segments. ${highPct}% are high-value and ${lowPct}% are low-value out of ${total} customers.`,
        actions: [
          'Nurture mid-value customers to move them to high-value',
          'Personalize offers based on each segment\'s purchase history',
          'Increase purchase frequency with targeted promotions'
        ]
      };
    }
  }
}
