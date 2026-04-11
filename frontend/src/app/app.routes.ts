import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/forecast', pathMatch: 'full' },
  {
    path: 'forecast',
    loadComponent: () => import('./pages/forecast/forecast.component').then(m => m.ForecastComponent)
  },
  {
    path: 'segmentation',
    loadComponent: () => import('./pages/segmentation/segmentation.component').then(m => m.SegmentationComponent)
  },
  {
    path: 'anomaly',
    loadComponent: () => import('./pages/anomaly/anomaly.component').then(m => m.AnomalyComponent)
  },
  {
    path: 'promotion',
    loadComponent: () => import('./pages/promotion/promotion.component').then(m => m.PromotionComponent)
  },
  {
    path: 'recommendations',
    loadComponent: () => import('./pages/recommendations/recommendations.component').then(m => m.RecommendationsComponent)
  },
  {
    path: 'sentiment',
    loadComponent: () => import('./pages/sentiment/sentiment.component').then(m => m.SentimentComponent)
  }
];
