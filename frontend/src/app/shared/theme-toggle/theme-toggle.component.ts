import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './theme-toggle.component.html',
  styleUrls: ['./theme-toggle.component.scss']
})
export class ThemeToggleComponent implements OnInit {
  isDarkMode = true;

  constructor(private themeService: ThemeService) {
    // Initialize immediately from service
    this.isDarkMode = this.themeService.getCurrentTheme();
  }

  ngOnInit(): void {
    this.themeService.isDarkMode$.subscribe(isDark => {
      this.isDarkMode = isDark;
      console.log('Theme changed to:', isDark ? 'dark' : 'light');
    });
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}
