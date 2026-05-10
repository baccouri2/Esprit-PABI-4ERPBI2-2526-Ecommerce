import { Component, OnInit, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { AuthService, UserRole } from '../../services/auth.service';
import { TranslationService } from '../../services/translation.service';
import { SdgFooterComponent } from '../../shared/sdg-footer/sdg-footer.component';


interface PowerBIReport {
  title: string;
  url: string;
  pageName: string;
}

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, SdgFooterComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit, AfterViewInit {
  @ViewChild('powerbiFrame') powerbiFrame!: ElementRef<HTMLIFrameElement>;
  
  powerBIUrl: SafeResourceUrl | null = null;
  reportTitle = '';
  isLoading = true;
  error = '';
  userRole: UserRole | null = null;
  userName = '';
  currentPageName = '';

  constructor(
    private sanitizer: DomSanitizer,
    private auth: AuthService,
    public translate: TranslationService
  ) {}

  ngOnInit() {
    this.loadDashboard();
  }

  ngAfterViewInit() {
    // Injecter du CSS dans l'iframe pour masquer les éléments de navigation
    this.injectIframeStyles();
  }

  /**
   * Fonction sécurisée qui retourne UNIQUEMENT le rapport autorisé pour le rôle donné
   * Utilise 3 rapports Power BI séparés pour une vraie sécurité
   */
  private getAuthorizedReport(role: UserRole): PowerBIReport | null {
    const baseParams = '&autoAuth=true&ctid=604f1a96-cbe8-43f8-abbf-f8eaf5d85730&filterPaneEnabled=false&navContentPaneEnabled=false';
    
    switch (role) {
      case 'ceo':
        return {
          title: 'CEO Dashboard',
          url: `https://app.powerbi.com/reportEmbed?reportId=0986f5fe-fe77-4e6f-b10d-520950dabb75${baseParams}`,
          pageName: 'CEO'
        };
      
      case 'sales_marketing':
        return {
          title: 'Sales & Marketing Dashboard',
          url: `https://app.powerbi.com/reportEmbed?reportId=3bd6183b-5fc7-4978-9517-08c7238a676e${baseParams}`,
          pageName: 'Sales'
        };
      
      case 'logistics_finance':
        return {
          title: 'Logistics & Finance Dashboard',
          url: `https://app.powerbi.com/reportEmbed?reportId=45348305-52d1-466f-9c69-2b5e84ae9d2f${baseParams}`,
          pageName: 'Logistics'
        };
      
      default:
        // Rôle inconnu → accès refusé
        return null;
    }
  }

  loadDashboard() {
    try {
      const user = this.auth.getCurrentUser();
      
      if (!user) {
        this.error = 'User not authenticated';
        this.isLoading = false;
        return;
      }

      this.userRole = user.role;
      this.userName = user.name;

      // Utilise la fonction sécurisée pour obtenir UNIQUEMENT le rapport autorisé
      const report = this.getAuthorizedReport(user.role);
      
      if (report) {
        this.reportTitle = report.title;
        this.currentPageName = report.pageName;
        this.powerBIUrl = this.sanitizer.bypassSecurityTrustResourceUrl(report.url);
        
        // Debug: Afficher l'URL chargée dans la console
        console.log('🎯 Dashboard loaded for:', user.name);
        console.log('📄 Page:', report.pageName);
        console.log('🔗 URL:', report.url);
      } else {
        this.error = 'No dashboard available for your role';
      }

      this.isLoading = false;
    } catch (err: any) {
      this.error = 'Failed to load dashboard';
      this.isLoading = false;
      console.error('Error loading dashboard:', err);
    }
  }

  injectIframeStyles() {
    // Attendre que l'iframe soit chargée
    setTimeout(() => {
      try {
        const iframe = this.powerbiFrame?.nativeElement;
        if (!iframe) return;

        // Injecter du CSS pour masquer les onglets de navigation et autres éléments
        const style = document.createElement('style');
        style.textContent = `
          /* Masquer tous les onglets de pages */
          .pbi-glyph-tab,
          .tab-button,
          .pageNavigator,
          .navigation-wrapper,
          [role="tablist"],
          .tabStrip {
            display: none !important;
            visibility: hidden !important;
          }
          
          /* Masquer les boutons de navigation */
          button[title*="page"],
          button[title*="Page"] {
            display: none !important;
          }
          
          /* Empêcher les clics sur les éléments de navigation */
          * {
            pointer-events: auto !important;
          }
        `;
        
        // Note: L'injection dans l'iframe est bloquée par CORS
        // La solution est d'utiliser les paramètres URL qui sont déjà en place
        console.log('Power BI iframe loaded with page:', this.currentPageName);
      } catch (e) {
        console.log('Cannot inject styles due to CORS, relying on URL parameters');
      }
    }, 2000);
  }

  onIframeLoad() {
    this.isLoading = false;
    this.injectIframeStyles();
  }

  onIframeError() {
    this.error = 'Unable to load Power BI dashboard. Please check your connection.';
    this.isLoading = false;
  }

  refreshDashboard() {
    this.isLoading = true;
    this.error = '';
    this.loadDashboard();
  }
}
