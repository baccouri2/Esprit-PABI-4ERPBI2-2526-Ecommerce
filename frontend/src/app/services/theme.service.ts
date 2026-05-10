import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private isDarkMode = new BehaviorSubject<boolean>(true);
  public isDarkMode$ = this.isDarkMode.asObservable();

  constructor() {
    this.loadTheme();
  }

  /**
   * Load theme from localStorage
   */
  private loadTheme(): void {
    const savedTheme = localStorage.getItem('theme');
    const isDark = savedTheme !== 'light';
    this.isDarkMode.next(isDark);
    this.applyTheme(isDark);
  }

  /**
   * Toggle between dark and light theme
   */
  toggleTheme(): void {
    const newTheme = !this.isDarkMode.value;
    this.isDarkMode.next(newTheme);
    this.applyTheme(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  }

  /**
   * Get current theme
   */
  getCurrentTheme(): boolean {
    return this.isDarkMode.value;
  }

  /**
   * Apply theme to document
   */
  private applyTheme(isDark: boolean): void {
    if (isDark) {
      document.body.classList.remove('light-theme');
      document.body.classList.add('dark-theme');
    } else {
      document.body.classList.remove('dark-theme');
      document.body.classList.add('light-theme');
    }
  }
}
