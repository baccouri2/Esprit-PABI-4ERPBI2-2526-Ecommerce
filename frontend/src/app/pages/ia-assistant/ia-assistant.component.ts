import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { TranslationService } from '../../services/translation.service';

// Import all page components
import { ForecastComponent } from '../forecast/forecast.component';
import { SegmentationComponent } from '../segmentation/segmentation.component';
import { AnomalyComponent } from '../anomaly/anomaly.component';
import { PromotionComponent } from '../promotion/promotion.component';
import { RecommendationsComponent } from '../recommendations/recommendations.component';
import { SentimentComponent } from '../sentiment/sentiment.component';

export interface Tab {
  id: string;
  label: string;
  icon: string;
  page: string; // matches PAGE_PERMISSIONS key
}

const ALL_TABS: Tab[] = [
  {
    id: 'forecast',
    label: 'Sales Forecasting',
    page: 'forecast',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`
  },
  {
    id: 'segmentation',
    label: 'Customer Insights',
    page: 'segmentation',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`
  },
  {
    id: 'anomaly',
    label: 'Transaction Monitor',
    page: 'anomaly',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
  },
  {
    id: 'promotion',
    label: 'Campaign Impact',
    page: 'promotion',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`
  },
  {
    id: 'recommendations',
    label: 'Smart Suggestions',
    page: 'recommendations',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
  },
  {
    id: 'sentiment',
    label: 'Customer Feedback',
    page: 'sentiment',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`
  }
];

@Component({
  selector: 'app-ia-assistant',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ForecastComponent,
    SegmentationComponent,
    AnomalyComponent,
    PromotionComponent,
    RecommendationsComponent,
    SentimentComponent
  ],
  templateUrl: './ia-assistant.component.html',
  styleUrls: ['./ia-assistant.component.scss']
})
export class IaAssistantComponent implements OnInit {
  tabs: Tab[] = [];
  activeTab = '';

  constructor(
    private auth: AuthService,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.tabs = ALL_TABS.filter(t => this.auth.canAccess(t.page));
    if (this.tabs.length > 0) {
      this.activeTab = this.tabs[0].id;
    }
  }

  setTab(id: string) { this.activeTab = id; }
}
