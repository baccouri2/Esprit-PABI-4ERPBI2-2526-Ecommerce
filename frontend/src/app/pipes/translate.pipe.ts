import { Pipe, PipeTransform, OnDestroy } from '@angular/core';
import { TranslationService } from '../services/translation.service';
import { Subscription } from 'rxjs';

@Pipe({
  name: 'translate',
  standalone: true,
  pure: false // Impure pipe to react to language changes
})
export class TranslatePipe implements PipeTransform, OnDestroy {
  private subscription: Subscription | null = null;
  private lastKey = '';
  private lastValue = '';

  constructor(private translationService: TranslationService) {
    // Subscribe to language changes
    this.subscription = this.translationService.currentLanguage$.subscribe(() => {
      // Force update when language changes
      if (this.lastKey) {
        this.lastValue = this.translationService.translate(this.lastKey);
      }
    });
  }

  transform(key: string): string {
    this.lastKey = key;
    this.lastValue = this.translationService.translate(key);
    return this.lastValue;
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }
}
