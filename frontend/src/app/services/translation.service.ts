import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type Language = 'en' | 'fr';

@Injectable({
  providedIn: 'root'
})
export class TranslationService {
  private currentLanguage = new BehaviorSubject<Language>('en');
  public currentLanguage$ = this.currentLanguage.asObservable();

  private translations: Record<Language, any> = {
    en: {},
    fr: {}
  };

  constructor() {
    this.loadTranslations();
    this.loadLanguage();
  }

  /**
   * Load language from localStorage
   */
  private loadLanguage(): void {
    const savedLang = localStorage.getItem('language') as Language;
    const lang = savedLang || 'en';
    this.currentLanguage.next(lang);
  }

  /**
   * Switch language
   */
  setLanguage(lang: Language): void {
    this.currentLanguage.next(lang);
    localStorage.setItem('language', lang);
  }

  /**
   * Get current language
   */
  getCurrentLanguage(): Language {
    return this.currentLanguage.value;
  }

  /**
   * Toggle between languages
   */
  toggleLanguage(): void {
    const newLang = this.currentLanguage.value === 'en' ? 'fr' : 'en';
    this.setLanguage(newLang);
  }

  /**
   * Get translation for a key
   */
  translate(key: string): string {
    const lang = this.currentLanguage.value;
    const keys = key.split('.');
    let value: any = this.translations[lang];

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key; // Return key if translation not found
      }
    }

    return typeof value === 'string' ? value : key;
  }

  /**
   * Get translation observable
   */
  translate$(key: string): Observable<string> {
    return new Observable(observer => {
      const subscription = this.currentLanguage$.subscribe(() => {
        observer.next(this.translate(key));
      });
      return () => subscription.unsubscribe();
    });
  }

  /**
   * Load all translations
   */
  private loadTranslations(): void {
    this.translations = {
      en: {
        // Common
        common: {
          loading: 'Loading...',
          error: 'Error',
          success: 'Success',
          cancel: 'Cancel',
          save: 'Save',
          delete: 'Delete',
          edit: 'Edit',
          create: 'Create',
          search: 'Search',
          filter: 'Filter',
          export: 'Export',
          import: 'Import',
          refresh: 'Refresh',
          close: 'Close',
          confirm: 'Confirm',
          yes: 'Yes',
          no: 'No',
          actions: 'Actions',
          details: 'Details',
          back: 'Back',
          next: 'Next',
          previous: 'Previous',
          submit: 'Submit',
          reset: 'Reset'
        },

        // Navigation
        nav: {
          dashboard: 'Dashboard',
          clients: 'Client Management',
          suppliers: 'Supplier Management',
          products: 'Product Management',
          orders: 'Order Management',
          crm: 'CRM Odoo',
          assistant: 'IA Assistant',
          logout: 'Sign Out',
          version: 'Version'
        },

        // Login
        login: {
          title: 'Sougui Analytics',
          subtitle: 'Sign in to your account',
          username: 'Username',
          password: 'Password',
          signIn: 'Sign In with Password',
          signInFace: 'Sign In with Face ID',
          registerFace: 'Register Your Face',
          faceId: 'Face ID',
          passwordLogin: 'Password',
          switchToLight: 'Switch to light mode',
          switchToDark: 'Switch to dark mode',
          availableAccounts: 'Available accounts:',
          ceo: 'CEO',
          sales: 'Sales',
          logistics: 'Logistics',
          errors: {
            invalidCredentials: 'Invalid username or password',
            enterCredentials: 'Please enter your username and password',
            noFaceRegistered: 'No face registered for this account. Please use password login and register your face first.',
            faceNotRecognized: 'Face not recognized within 15 seconds. Please try again or use password login.',
            cameraError: 'Camera error'
          },
          faceRecognition: {
            registerTitle: 'Register Your Face',
            verifyTitle: 'Verify Your Face',
            faceDetected: 'Face Detected',
            noFaceDetected: 'No Face Detected',
            secondsRemaining: 'seconds remaining',
            registrationMode: 'Registration Mode: Position your face in the frame. Hold still for 2 seconds.',
            verificationMode: 'Verification Mode: Position your face to verify and login.',
            initializingCamera: 'Initializing camera...',
            faceRegistered: 'Face registered successfully! You can now use Face ID to login.',
            clearFace: 'Clear Face',
            positionFace: 'Position your face in front of the camera',
            timeoutInfo: 'You have 15 seconds to verify'
          }
        },

        // Dashboard
        dashboard: {
          title: 'Dashboard',
          subtitle: 'Overview of your business metrics',
          welcome: 'Welcome back',
          loading: 'Loading Power BI dashboard...',
          error: 'Please check your connection or contact the administrator.',
          metrics: {
            totalRevenue: 'Total Revenue',
            totalOrders: 'Total Orders',
            activeClients: 'Active Clients',
            products: 'Products'
          }
        },

        // Clients
        clients: {
          title: 'Client Management',
          subtitle: 'Manage your customer database',
          addClient: 'Add Client',
          editClient: 'Edit Client',
          deleteClient: 'Delete Client',
          clientName: 'Client Name',
          email: 'Email',
          phone: 'Phone',
          address: 'Address',
          status: 'Status',
          actions: 'Actions',
          confirmDelete: 'Are you sure you want to delete this client?',
          active: 'Active',
          inactive: 'Inactive',
          searchPlaceholder: 'Search clients...',
          addB2B: 'Add B2B',
          addB2C: 'Add B2C',
          noClients: 'No clients found.',
          viewOnly: 'View Only',
          kpi: {
            totalClients: 'Total Clients',
            b2bClients: 'B2B Clients',
            b2cClients: 'B2C Clients'
          },
          filters: {
            all: 'All',
            b2b: 'B2B',
            b2c: 'B2C'
          },
          table: {
            type: 'Type',
            nameCompany: 'Name / Company',
            mfDetails: 'MF / Details',
            participationDate: 'Participation Date',
            orders: 'Orders'
          },
          modal: {
            add: 'Add',
            edit: 'Edit',
            client: 'Client',
            mf: 'MF (Matricule Fiscal)',
            mfPlaceholder: 'e.g. 000121J/P/M000',
            companyName: 'Company Name',
            companyPlaceholder: 'e.g. Attijari Bank',
            firstName: 'First Name',
            firstNamePlaceholder: 'e.g. Haifa',
            lastName: 'Last Name',
            lastNamePlaceholder: 'e.g. Zou',
            participationDate: 'Participation Date',
            saving: 'Saving...',
            saveChanges: 'Save Changes'
          },
          deleteModal: {
            title: 'Delete Client',
            confirmText: 'Are you sure you want to delete',
            warning: 'This action cannot be undone.',
            deleting: 'Deleting...'
          }
        },

        // Suppliers
        suppliers: {
          title: 'Supplier Management',
          subtitle: 'Manage your supplier network',
          addSupplier: 'Add Supplier',
          editSupplier: 'Edit Supplier',
          deleteSupplier: 'Delete Supplier',
          supplierName: 'Supplier Name',
          email: 'Email',
          phone: 'Phone',
          address: 'Address',
          status: 'Status',
          actions: 'Actions',
          confirmDelete: 'Are you sure you want to delete this supplier?',
          totalSuppliers: 'Total Suppliers',
          withPurchases: 'With Purchases',
          noSuppliers: 'No suppliers found.',
          table: {
            name: 'Name',
            company: 'Company',
            paymentMethod: 'Payment Method',
            purchases: 'Purchases'
          },
          modal: {
            addTitle: 'Add Supplier',
            editTitle: 'Edit Supplier',
            supplierName: 'Supplier Name',
            supplierNamePlaceholder: 'e.g. SMPA',
            company: 'Company',
            companyPlaceholder: 'e.g. SMPA Corp',
            paymentMethod: 'Payment Method',
            selectPayment: '-- Select --',
            saving: 'Saving...',
            saveChanges: 'Save Changes'
          },
          deleteModal: {
            title: 'Delete Supplier',
            confirmText: 'Delete',
            warning: 'This action cannot be undone.',
            deleting: 'Deleting...'
          }
        },

        // Products
        products: {
          title: 'Product Management',
          subtitle: 'Manage your product catalog',
          addProduct: 'Add Product',
          editProduct: 'Edit Product',
          deleteProduct: 'Delete Product',
          productName: 'Product Name',
          category: 'Category',
          price: 'Price',
          stock: 'Stock',
          status: 'Status',
          actions: 'Actions',
          confirmDelete: 'Are you sure you want to delete this product?',
          searchPlaceholder: 'Search by name or reference...',
          allCategories: 'All Categories',
          clear: 'Clear',
          noProducts: 'No products found.',
          kpi: {
            totalProducts: 'Total Products',
            categories: 'Categories',
            withSales: 'With Sales'
          },
          table: {
            reference: 'Reference',
            productName: 'Product Name',
            category: 'Category',
            sales: 'Sales'
          },
          modal: {
            addTitle: 'Add Product',
            editTitle: 'Edit Product',
            productName: 'Product Name',
            productNamePlaceholder: 'e.g. Bougie parfumée rose',
            reference: 'Reference',
            referencePlaceholder: 'e.g. REF-001',
            category: 'Category',
            selectCategory: '-- Select category --',
            saving: 'Saving...',
            saveChanges: 'Save Changes'
          },
          deleteModal: {
            title: 'Delete Product',
            confirmText: 'Delete',
            warning: 'This action cannot be undone.',
            deleting: 'Deleting...'
          }
        },

        // Orders
        orders: {
          title: 'Order Management',
          subtitle: 'Track and manage customer orders',
          addOrder: 'Add Order',
          editOrder: 'Edit Order',
          deleteOrder: 'Delete Order',
          orderNumber: 'Order #',
          client: 'Client',
          date: 'Date',
          amount: 'Amount',
          status: 'Status',
          actions: 'Actions',
          confirmDelete: 'Are you sure you want to delete this order?',
          pending: 'Pending',
          processing: 'Processing',
          completed: 'Completed',
          cancelled: 'Cancelled',
          searchPlaceholder: 'Search by order ID, delivery number, or company...',
          allStatuses: 'All Statuses',
          clear: 'Clear',
          refresh: 'Refresh',
          newOrder: 'New Order',
          loading: 'Loading orders...',
          noOrders: 'No orders found',
          viewOnly: 'View Only',
          table: {
            id: 'ID',
            orderNumber: 'Order #',
            status: 'Status',
            date: 'Date',
            delivery: 'Delivery',
            items: 'Items',
            total: 'Total'
          },
          modal: {
            createTitle: 'Create New Order',
            editTitle: 'Edit Order',
            viewTitle: 'Order Details',
            orderId: 'Order ID',
            orderIdPlaceholder: 'e.g., FAC25-001',
            status: 'Status',
            date: 'Date',
            deliveryId: 'Delivery ID',
            deliveryIdPlaceholder: 'Enter delivery ID',
            deliveryCompany: 'Delivery Company',
            deliveryCost: 'Delivery Cost',
            client: 'Client',
            orderItems: 'Order Items',
            reference: 'Reference',
            description: 'Description',
            unitPrice: 'Unit Price',
            quantity: 'Quantity',
            total: 'Total',
            create: 'Create',
            update: 'Update',
            close: 'Close',
            downloadInvoice: 'Download Invoice'
          }
        },

        // CRM
        crm: {
          title: 'CRM - Sales Pipeline',
          subtitle: 'Build customer loyalty and strengthen relationships',
          newOpportunity: 'New Opportunity',
          newCustomer: 'New Customer',
          stages: {
            new: 'New',
            qualified: 'Qualified',
            proposition: 'Proposition',
            won: 'Won'
          },
          opportunityName: 'Opportunity Name',
          customerName: 'Customer Name',
          expectedRevenue: 'Expected Revenue',
          probability: 'Probability',
          stage: 'Stage',
          customer: 'Customer',
          email: 'Email',
          phone: 'Phone',
          createOpportunity: 'Create Opportunity',
          editOpportunity: 'Edit Opportunity',
          createCustomer: 'Create Customer',
          deleteConfirm: 'Are you sure you want to delete this opportunity?',
          loading: 'Loading opportunities...',
          error: 'Error loading opportunities'
        },

        // IA Assistant
        assistant: {
          title: 'IA Assistant',
          subtitle: 'AI-powered business insights and predictions',
          tabs: {
            forecast: 'Sales Forecasting',
            recommendations: 'Smart Suggestions',
            sentiment: 'Customer Feedback',
            competition: 'Competition Analysis',
            promotion: 'Campaign Impact',
            segmentation: 'Customer Insights',
            anomaly: 'Transaction Monitor'
          },
          forecast: {
            title: 'Sales Forecasting',
            description: 'Predict future sales trends',
            selectProduct: 'Select Product',
            weeks: 'Number of Weeks',
            generate: 'Generate Forecast',
            week: 'Week',
            quantity: 'Quantity',
            units: 'units',
            predictionMethod: 'Prediction Method',
            weeksToForecast: 'Weeks to Forecast',
            generateForecast: 'Generate Forecast',
            analyzing: 'Analyzing...',
            predictedSales: 'Predicted Sales',
            historicalPerformance: 'Historical Performance',
            salesVolume: 'Sales Volume',
            weekOf: 'Week of',
            forecastSettings: 'Forecast Settings'
          },
          recommendations: {
            title: 'Product Recommendations',
            description: 'Get personalized product suggestions',
            selectClient: 'Select Client',
            getRecommendations: 'Get Recommendations',
            recommendedProducts: 'Recommended Products',
            score: 'Score'
          },
          sentiment: {
            title: 'Customer Feedback',
            description: 'Analyze customer feedback sentiment',
            enterText: 'Enter text to analyze',
            analyze: 'Analyze Sentiment',
            result: 'Sentiment Result',
            positive: 'Positive',
            negative: 'Negative',
            confidence: 'Confidence',
            feedbackAnalyzerStatus: 'Feedback Analyzer Status',
            accuracy: 'Accuracy',
            trainingSamples: 'Training Samples',
            positiveReviews: 'Positive Reviews',
            negativeFeedback: 'Negative Feedback',
            analyzeCustomFeedback: 'Analyze Custom Feedback',
            customFeedbackDesc: 'Enter customer feedback to analyze its sentiment',
            feedbackPlaceholder: 'Type or paste customer feedback here...',
            analyzeFeedback: 'Analyze Feedback',
            analyzing: 'Analyzing...',
            sentiment: 'Sentiment',
            confident: 'confident',
            analyzeAllClaims: 'Analyze All Customer Claims',
            allClaimsDesc: 'Review sentiment across all recorded customer feedback',
            analyzeAllFeedback: 'Analyze All Feedback',
            processing: 'Processing...',
            totalFeedback: 'Total Feedback',
            satisfactionRate: 'Satisfaction Rate',
            feedbackDetails: 'Feedback Details'
          },
          competition: {
            title: 'Competition Analysis',
            description: 'Analyze market competition',
            analyze: 'Analyze Competition'
          },
          promotion: {
            title: 'Promotion Optimizer',
            description: 'Optimize your promotional campaigns',
            optimize: 'Optimize Promotions'
          }
        },

        // Chatbot
        chatbot: {
          title: 'Data Assistant',
          placeholder: 'Ask about your data...',
          send: 'Send',
          askData: 'Ask Data',
          dataAssistant: 'Data Assistant',
          connectedTo: 'Connected to dw_pi',
          clearChat: 'Clear chat',
          summarize: '✨ Summarize',
          summarizing: 'Summarizing...',
          summarizeTitle: 'Generate a full database summary',
          uploadFile: '📎 Upload File',
          analyzing: 'Analyzing...',
          uploadTitle: 'Upload a CSV or PDF file for analysis',
          summaryTag: '✨ Summary',
          fileTag: '📎 File Analysis'
        },

        // User Roles
        roles: {
          ceo: 'CEO',
          sales_marketing: 'Sales & Marketing Manager',
          logistics_finance: 'Logistics & Finance Manager'
        }
      },

      fr: {
        // Commun
        common: {
          loading: 'Chargement...',
          error: 'Erreur',
          success: 'Succès',
          cancel: 'Annuler',
          save: 'Enregistrer',
          delete: 'Supprimer',
          edit: 'Modifier',
          create: 'Créer',
          search: 'Rechercher',
          filter: 'Filtrer',
          export: 'Exporter',
          import: 'Importer',
          refresh: 'Actualiser',
          close: 'Fermer',
          confirm: 'Confirmer',
          yes: 'Oui',
          no: 'Non',
          actions: 'Actions',
          details: 'Détails',
          back: 'Retour',
          next: 'Suivant',
          previous: 'Précédent',
          submit: 'Soumettre',
          reset: 'Réinitialiser'
        },

        // Navigation
        nav: {
          dashboard: 'Tableau de bord',
          clients: 'Gestion des clients',
          suppliers: 'Gestion des fournisseurs',
          products: 'Gestion des produits',
          orders: 'Gestion des commandes',
          crm: 'CRM Odoo',
          assistant: 'Assistant IA',
          logout: 'Déconnexion',
          version: 'Version'
        },

        // Connexion
        login: {
          title: 'Sougui Analytics',
          subtitle: 'Connectez-vous à votre compte',
          username: "Nom d'utilisateur",
          password: 'Mot de passe',
          signIn: 'Se connecter avec mot de passe',
          signInFace: 'Se connecter avec Face ID',
          registerFace: 'Enregistrer votre visage',
          faceId: 'Face ID',
          passwordLogin: 'Mot de passe',
          switchToLight: 'Passer en mode clair',
          switchToDark: 'Passer en mode sombre',
          availableAccounts: 'Comptes disponibles :',
          ceo: 'PDG',
          sales: 'Ventes',
          logistics: 'Logistique',
          errors: {
            invalidCredentials: "Nom d'utilisateur ou mot de passe invalide",
            enterCredentials: "Veuillez entrer votre nom d'utilisateur et mot de passe",
            noFaceRegistered: "Aucun visage enregistré pour ce compte. Veuillez utiliser la connexion par mot de passe et enregistrer votre visage d'abord.",
            faceNotRecognized: 'Visage non reconnu dans les 15 secondes. Veuillez réessayer ou utiliser la connexion par mot de passe.',
            cameraError: 'Erreur de caméra'
          },
          faceRecognition: {
            registerTitle: 'Enregistrer votre visage',
            verifyTitle: 'Vérifier votre visage',
            faceDetected: 'Visage détecté',
            noFaceDetected: 'Aucun visage détecté',
            secondsRemaining: 'secondes restantes',
            registrationMode: 'Mode enregistrement : Positionnez votre visage dans le cadre. Restez immobile pendant 2 secondes.',
            verificationMode: 'Mode vérification : Positionnez votre visage pour vérifier et vous connecter.',
            initializingCamera: 'Initialisation de la caméra...',
            faceRegistered: 'Visage enregistré avec succès ! Vous pouvez maintenant utiliser Face ID pour vous connecter.',
            clearFace: 'Effacer le visage',
            positionFace: 'Positionnez votre visage devant la caméra',
            timeoutInfo: 'Vous avez 15 secondes pour vérifier'
          }
        },

        // Tableau de bord
        dashboard: {
          title: 'Tableau de bord',
          subtitle: 'Vue d\'ensemble de vos métriques commerciales',
          welcome: 'Bon retour',
          loading: 'Chargement du tableau de bord Power BI...',
          error: 'Veuillez vérifier votre connexion ou contacter l\'administrateur.',
          metrics: {
            totalRevenue: 'Chiffre d\'affaires total',
            totalOrders: 'Commandes totales',
            activeClients: 'Clients actifs',
            products: 'Produits'
          }
        },

        // Clients
        clients: {
          title: 'Gestion des clients',
          subtitle: 'Gérez votre base de données clients',
          addClient: 'Ajouter un client',
          editClient: 'Modifier le client',
          deleteClient: 'Supprimer le client',
          clientName: 'Nom du client',
          email: 'Email',
          phone: 'Téléphone',
          address: 'Adresse',
          status: 'Statut',
          actions: 'Actions',
          confirmDelete: 'Êtes-vous sûr de vouloir supprimer ce client ?',
          active: 'Actif',
          inactive: 'Inactif',
          searchPlaceholder: 'Rechercher des clients...',
          addB2B: 'Ajouter B2B',
          addB2C: 'Ajouter B2C',
          noClients: 'Aucun client trouvé.',
          viewOnly: 'Lecture seule',
          kpi: {
            totalClients: 'Clients totaux',
            b2bClients: 'Clients B2B',
            b2cClients: 'Clients B2C'
          },
          filters: {
            all: 'Tous',
            b2b: 'B2B',
            b2c: 'B2C'
          },
          table: {
            type: 'Type',
            nameCompany: 'Nom / Entreprise',
            mfDetails: 'MF / Détails',
            participationDate: 'Date de participation',
            orders: 'Commandes'
          },
          modal: {
            add: 'Ajouter',
            edit: 'Modifier',
            client: 'Client',
            mf: 'MF (Matricule Fiscal)',
            mfPlaceholder: 'ex. 000121J/P/M000',
            companyName: 'Nom de l\'entreprise',
            companyPlaceholder: 'ex. Attijari Bank',
            firstName: 'Prénom',
            firstNamePlaceholder: 'ex. Haifa',
            lastName: 'Nom',
            lastNamePlaceholder: 'ex. Zou',
            participationDate: 'Date de participation',
            saving: 'Enregistrement...',
            saveChanges: 'Enregistrer les modifications'
          },
          deleteModal: {
            title: 'Supprimer le client',
            confirmText: 'Êtes-vous sûr de vouloir supprimer',
            warning: 'Cette action ne peut pas être annulée.',
            deleting: 'Suppression...'
          }
        },

        // Fournisseurs
        suppliers: {
          title: 'Gestion des fournisseurs',
          subtitle: 'Gérez votre réseau de fournisseurs',
          addSupplier: 'Ajouter un fournisseur',
          editSupplier: 'Modifier le fournisseur',
          deleteSupplier: 'Supprimer le fournisseur',
          supplierName: 'Nom du fournisseur',
          email: 'Email',
          phone: 'Téléphone',
          address: 'Adresse',
          status: 'Statut',
          actions: 'Actions',
          confirmDelete: 'Êtes-vous sûr de vouloir supprimer ce fournisseur ?',
          totalSuppliers: 'Fournisseurs totaux',
          withPurchases: 'Avec achats',
          noSuppliers: 'Aucun fournisseur trouvé.',
          table: {
            name: 'Nom',
            company: 'Entreprise',
            paymentMethod: 'Mode de paiement',
            purchases: 'Achats'
          },
          modal: {
            addTitle: 'Ajouter un fournisseur',
            editTitle: 'Modifier le fournisseur',
            supplierName: 'Nom du fournisseur',
            supplierNamePlaceholder: 'ex. SMPA',
            company: 'Entreprise',
            companyPlaceholder: 'ex. SMPA Corp',
            paymentMethod: 'Mode de paiement',
            selectPayment: '-- Sélectionner --',
            saving: 'Enregistrement...',
            saveChanges: 'Enregistrer les modifications'
          },
          deleteModal: {
            title: 'Supprimer le fournisseur',
            confirmText: 'Supprimer',
            warning: 'Cette action ne peut pas être annulée.',
            deleting: 'Suppression...'
          }
        },

        // Produits
        products: {
          title: 'Gestion des produits',
          subtitle: 'Gérez votre catalogue de produits',
          addProduct: 'Ajouter un produit',
          editProduct: 'Modifier le produit',
          deleteProduct: 'Supprimer le produit',
          productName: 'Nom du produit',
          category: 'Catégorie',
          price: 'Prix',
          stock: 'Stock',
          status: 'Statut',
          actions: 'Actions',
          confirmDelete: 'Êtes-vous sûr de vouloir supprimer ce produit ?',
          searchPlaceholder: 'Rechercher par nom ou référence...',
          allCategories: 'Toutes les catégories',
          clear: 'Effacer',
          noProducts: 'Aucun produit trouvé.',
          kpi: {
            totalProducts: 'Produits totaux',
            categories: 'Catégories',
            withSales: 'Avec ventes'
          },
          table: {
            reference: 'Référence',
            productName: 'Nom du produit',
            category: 'Catégorie',
            sales: 'Ventes'
          },
          modal: {
            addTitle: 'Ajouter un produit',
            editTitle: 'Modifier le produit',
            productName: 'Nom du produit',
            productNamePlaceholder: 'ex. Bougie parfumée rose',
            reference: 'Référence',
            referencePlaceholder: 'ex. REF-001',
            category: 'Catégorie',
            selectCategory: '-- Sélectionner une catégorie --',
            saving: 'Enregistrement...',
            saveChanges: 'Enregistrer les modifications'
          },
          deleteModal: {
            title: 'Supprimer le produit',
            confirmText: 'Supprimer',
            warning: 'Cette action ne peut pas être annulée.',
            deleting: 'Suppression...'
          }
        },

        // Commandes
        orders: {
          title: 'Gestion des commandes',
          subtitle: 'Suivez et gérez les commandes clients',
          addOrder: 'Ajouter une commande',
          editOrder: 'Modifier la commande',
          deleteOrder: 'Supprimer la commande',
          orderNumber: 'Commande n°',
          client: 'Client',
          date: 'Date',
          amount: 'Montant',
          status: 'Statut',
          actions: 'Actions',
          confirmDelete: 'Êtes-vous sûr de vouloir supprimer cette commande ?',
          pending: 'En attente',
          processing: 'En cours',
          completed: 'Terminée',
          cancelled: 'Annulée',
          searchPlaceholder: 'Rechercher par ID de commande, numéro de livraison ou entreprise...',
          allStatuses: 'Tous les statuts',
          clear: 'Effacer',
          refresh: 'Actualiser',
          newOrder: 'Nouvelle commande',
          loading: 'Chargement des commandes...',
          noOrders: 'Aucune commande trouvée',
          viewOnly: 'Lecture seule',
          table: {
            id: 'ID',
            orderNumber: 'Commande n°',
            status: 'Statut',
            date: 'Date',
            delivery: 'Livraison',
            items: 'Articles',
            total: 'Total'
          },
          modal: {
            createTitle: 'Créer une nouvelle commande',
            editTitle: 'Modifier la commande',
            viewTitle: 'Détails de la commande',
            orderId: 'ID de commande',
            orderIdPlaceholder: 'ex., FAC25-001',
            status: 'Statut',
            date: 'Date',
            deliveryId: 'ID de livraison',
            deliveryIdPlaceholder: 'Entrez l\'ID de livraison',
            deliveryCompany: 'Entreprise de livraison',
            deliveryCost: 'Coût de livraison',
            client: 'Client',
            orderItems: 'Articles de la commande',
            reference: 'Référence',
            description: 'Description',
            unitPrice: 'Prix unitaire',
            quantity: 'Quantité',
            total: 'Total',
            create: 'Créer',
            update: 'Mettre à jour',
            close: 'Fermer',
            downloadInvoice: 'Télécharger la facture'
          }
        },

        // CRM
        crm: {
          title: 'CRM - Pipeline de ventes',
          subtitle: 'Fidéliser votre client et renforcer vos relations',
          newOpportunity: 'Nouvelle opportunité',
          newCustomer: 'Nouveau client',
          stages: {
            new: 'Nouveau',
            qualified: 'Qualifié',
            proposition: 'Proposition',
            won: 'Gagné'
          },
          opportunityName: 'Nom de l\'opportunité',
          customerName: 'Nom du client',
          expectedRevenue: 'Revenu attendu',
          probability: 'Probabilité',
          stage: 'Étape',
          customer: 'Client',
          email: 'Email',
          phone: 'Téléphone',
          createOpportunity: 'Créer une opportunité',
          editOpportunity: 'Modifier l\'opportunité',
          createCustomer: 'Créer un client',
          deleteConfirm: 'Êtes-vous sûr de vouloir supprimer cette opportunité ?',
          loading: 'Chargement des opportunités...',
          error: 'Erreur lors du chargement des opportunités'
        },

        // Assistant IA
        assistant: {
          title: 'Assistant IA',
          subtitle: 'Insights et prédictions commerciales alimentés par l\'IA',
          tabs: {
            forecast: 'Prévisions de ventes',
            recommendations: 'Suggestions intelligentes',
            sentiment: 'Retours clients',
            competition: 'Analyse de la concurrence',
            promotion: 'Impact des campagnes',
            segmentation: 'Insights clients',
            anomaly: 'Surveillance des transactions'
          },
          forecast: {
            title: 'Prévisions de ventes',
            description: 'Prédire les tendances de ventes futures',
            selectProduct: 'Sélectionner un produit',
            weeks: 'Nombre de semaines',
            generate: 'Générer les prévisions',
            week: 'Semaine',
            quantity: 'Quantité',
            units: 'unités',
            predictionMethod: 'Méthode de prédiction',
            weeksToForecast: 'Semaines à prévoir',
            generateForecast: 'Générer les prévisions',
            analyzing: 'Analyse en cours...',
            predictedSales: 'Ventes prévues',
            historicalPerformance: 'Performance historique',
            salesVolume: 'Volume des ventes',
            weekOf: 'Semaine du',
            forecastSettings: 'Paramètres de prévision'
          },
          recommendations: {
            title: 'Recommandations de produits',
            description: 'Obtenez des suggestions de produits personnalisées',
            selectClient: 'Sélectionner un client',
            getRecommendations: 'Obtenir des recommandations',
            recommendedProducts: 'Produits recommandés',
            score: 'Score'
          },
          sentiment: {
            title: 'Retours clients',
            description: 'Analyser le sentiment des retours clients',
            enterText: 'Entrez le texte à analyser',
            analyze: 'Analyser le sentiment',
            result: 'Résultat du sentiment',
            positive: 'Positif',
            negative: 'Négatif',
            confidence: 'Confiance',
            feedbackAnalyzerStatus: 'Statut de l\'analyseur de retours',
            accuracy: 'Précision',
            trainingSamples: 'Échantillons d\'entraînement',
            positiveReviews: 'Avis positifs',
            negativeFeedback: 'Retours négatifs',
            analyzeCustomFeedback: 'Analyser un retour personnalisé',
            customFeedbackDesc: 'Entrez un retour client pour analyser son sentiment',
            feedbackPlaceholder: 'Tapez ou collez le retour client ici...',
            analyzeFeedback: 'Analyser le retour',
            analyzing: 'Analyse en cours...',
            sentiment: 'Sentiment',
            confident: 'de confiance',
            analyzeAllClaims: 'Analyser toutes les réclamations clients',
            allClaimsDesc: 'Examiner le sentiment de tous les retours clients enregistrés',
            analyzeAllFeedback: 'Analyser tous les retours',
            processing: 'Traitement en cours...',
            totalFeedback: 'Retours totaux',
            satisfactionRate: 'Taux de satisfaction',
            feedbackDetails: 'Détails des retours'
          },
          competition: {
            title: 'Analyse de la concurrence',
            description: 'Analyser la concurrence du marché',
            analyze: 'Analyser la concurrence'
          },
          promotion: {
            title: 'Optimiseur de promotions',
            description: 'Optimisez vos campagnes promotionnelles',
            optimize: 'Optimiser les promotions'
          }
        },

        // Chatbot
        chatbot: {
          title: 'Assistant de données',
          placeholder: 'Posez une question sur vos données...',
          send: 'Envoyer',
          askData: 'Interroger les données',
          dataAssistant: 'Assistant de données',
          connectedTo: 'Connecté à dw_pi',
          clearChat: 'Effacer la conversation',
          summarize: '✨ Résumer',
          summarizing: 'Résumé en cours...',
          summarizeTitle: 'Générer un résumé complet de la base de données',
          uploadFile: '📎 Télécharger un fichier',
          analyzing: 'Analyse en cours...',
          uploadTitle: 'Télécharger un fichier CSV ou PDF pour analyse',
          summaryTag: '✨ Résumé',
          fileTag: '📎 Analyse de fichier'
        },

        // Rôles utilisateur
        roles: {
          ceo: 'PDG',
          sales_marketing: 'Responsable Ventes & Marketing',
          logistics_finance: 'Responsable Logistique & Finance'
        }
      }
    };
  }
}
