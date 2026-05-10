import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ChatbotComponent } from './shared/chatbot/chatbot.component';
import { ThemeToggleComponent } from './shared/theme-toggle/theme-toggle.component';
import { LanguageSwitcherComponent } from './shared/language-switcher/language-switcher.component';
import { AuthService, User, PAGE_PERMISSIONS, UserRole } from './services/auth.service';
import { TranslationService } from './services/translation.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ChatbotComponent, ThemeToggleComponent, LanguageSwitcherComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  menuOpen  = false;
  user: User | null = null;
  isLoginPage = false;

  constructor(
    private auth: AuthService, 
    private router: Router,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.user = this.auth.getCurrentUser();
    this.router.events.subscribe(() => {
      this.user = this.auth.getCurrentUser();
      this.isLoginPage = this.router.url === '/login';
    });
  }

  toggleMenu() { this.menuOpen = !this.menuOpen; }

  logout() { this.auth.logout(); }

  canSee(page: string): boolean { return this.auth.canAccess(page); }

  canAccessCRM(): boolean {
    return this.user?.role === 'ceo';
  }

  getRoleBadge(): string {
    if (!this.user) return '';
    const roleKey = `roles.${this.user.role}` as const;
    return this.translate.translate(roleKey);
  }

  getRoleColor(): string {
    if (!this.user) return '';
    const map: Record<UserRole, string> = {
      ceo:                '#c084fc',
      sales_marketing:    '#60a5fa',
      logistics_finance:  '#34d399'
    };
    return map[this.user.role] || '#fff';
  }
}
