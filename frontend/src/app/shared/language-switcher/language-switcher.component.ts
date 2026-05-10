import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslationService, Language } from '../../services/translation.service';

@Component({
  selector: 'app-language-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './language-switcher.component.html',
  styleUrls: ['./language-switcher.component.scss']
})
export class LanguageSwitcherComponent implements OnInit {
  currentLanguage: Language = 'en';

  constructor(private translationService: TranslationService) {
    // Initialize immediately from service
    this.currentLanguage = this.translationService.getCurrentLanguage();
  }

  ngOnInit(): void {
    this.translationService.currentLanguage$.subscribe(lang => {
      this.currentLanguage = lang;
      console.log('Language changed to:', lang);
    });
  }

  toggleLanguage(): void {
    this.translationService.toggleLanguage();
  }

  get languageLabel(): string {
    // Show the language you'll GET when you click (opposite of current)
    return this.currentLanguage === 'en' ? 'FR' : 'EN';
  }

  get languageTooltip(): string {
    return this.currentLanguage === 'en' 
      ? 'Passer en français' 
      : 'Switch to English';
  }
}
