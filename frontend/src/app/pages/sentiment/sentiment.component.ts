import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdvicePopupComponent, Advice } from '../../shared/advice-popup/advice-popup.component';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';

@Component({
  selector: 'app-sentiment',
  standalone: true,
  imports: [CommonModule, FormsModule, AdvicePopupComponent],
  templateUrl: './sentiment.component.html',
  styleUrls: ['./sentiment.component.scss']
})
export class SentimentComponent implements OnInit {
  loadingTrain   = false;
  loadingAnalyze = false;
  loadingBatch   = false;
  error = '';
  advice: Advice | null = null;

  userText = '';
  singleResult: any = null;
  batchResults: any[] = [];
  summary: any = null;
  trainingStats: any = null;

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  ngOnInit() { this.trainModel(); }

  trainModel() {
    this.loadingTrain = true;
    this.api.trainSentiment().subscribe({
      next: (res) => { this.trainingStats = res; this.loadingTrain = false; },
      error: () => { this.error = 'Unable to train feedback analyzer'; this.loadingTrain = false; }
    });
  }

  analyzeText() {
    if (!this.userText.trim()) { this.error = 'Please enter some text to analyze'; return; }
    if (this.userText.trim().length < 5) { this.error = 'Text must be at least 5 characters'; return; }
    this.loadingAnalyze = true;
    this.error = '';
    this.singleResult = null;
    this.api.analyzeSentiment(this.userText).subscribe({
      next: (res) => {
        this.singleResult = res.result;
        this.loadingAnalyze = false;
        this.buildSingleAdvice();
      },
      error: (err) => { this.error = err.error?.error || 'Analysis failed'; this.loadingAnalyze = false; }
    });
  }

  analyzeBatch() {
    this.loadingBatch = true;
    this.error = '';
    this.batchResults = [];
    this.summary = null;
    this.api.analyzeSentimentBatch().subscribe({
      next: (res) => {
        this.batchResults = res.results || [];
        this.summary = res.summary;
        this.loadingBatch = false;
        this.buildBatchAdvice();
      },
      error: (err) => { this.error = err.error?.error || 'Batch analysis failed'; this.loadingBatch = false; }
    });
  }

  getSentimentClass(sentiment: string): string {
    return sentiment === 'Positive' ? 'badge-success' : 'badge-danger';
  }

  private buildSingleAdvice() {
    if (!this.singleResult) return;
    const { sentiment, confidence } = this.singleResult;
    if (sentiment === 'Positive') {
      this.advice = {
        type: 'success',
        title: 'Positive Feedback Detected',
        message: `This feedback is positive with ${confidence}% confidence. Happy customers are your best advocates — make the most of this sentiment.`,
        actions: [
          'Ask this customer for a public review or testimonial',
          'Use this feedback in your marketing materials',
          'Identify what made them happy and replicate it'
        ]
      };
    } else {
      this.advice = {
        type: 'danger',
        title: 'Negative Feedback Detected',
        message: `This feedback is negative with ${confidence}% confidence. Address this concern promptly to prevent churn and protect your brand reputation.`,
        actions: [
          'Reach out to the customer with a resolution offer',
          'Identify the root cause of the complaint',
          'Log this issue to track recurring problems'
        ]
      };
    }
  }

  private buildBatchAdvice() {
    if (!this.summary) return;
    const rate = this.summary.positive_rate;
    const total = this.summary.total;
    if (rate >= 60) {
      this.advice = {
        type: 'success',
        title: 'Overall Positive Customer Sentiment',
        message: `${rate}% of ${total} feedback entries are positive. Your customers are generally satisfied — a great sign for retention and growth.`,
        actions: [
          'Highlight positive feedback in your next marketing campaign',
          'Reward your team for maintaining high satisfaction',
          'Focus on converting the remaining negative feedback'
        ]
      };
    } else if (rate >= 40) {
      this.advice = {
        type: 'warning',
        title: 'Mixed Customer Sentiment',
        message: `Only ${rate}% of feedback is positive out of ${total} entries. There is significant room for improvement in customer satisfaction.`,
        actions: [
          'Review the negative feedback for common themes',
          'Prioritize resolving the most frequent complaints',
          'Set a target to reach 70% positive feedback within 3 months'
        ]
      };
    } else {
      this.advice = {
        type: 'danger',
        title: 'Predominantly Negative Feedback',
        message: `Only ${rate}% of ${total} feedback entries are positive. This is a critical signal — customer dissatisfaction is widespread.`,
        actions: [
          'Conduct an urgent customer satisfaction survey',
          'Identify and fix the top 3 recurring complaints immediately',
          'Consider a customer recovery program with special offers',
          'Review product quality and delivery processes'
        ]
      };
    }
  }
}
