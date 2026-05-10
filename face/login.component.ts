import { Component, ViewChild, ElementRef, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { FaceRecognitionService } from '../../services/face-recognition.service';
import { ThemeService } from '../../services/theme.service';
import { TranslationService } from '../../services/translation.service';
import { LanguageSwitcherComponent } from '../../shared/language-switcher/language-switcher.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, LanguageSwitcherComponent],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, OnDestroy {
  @ViewChild('videoElement') videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasElement') canvasElement!: ElementRef<HTMLCanvasElement>;

  username = '';
  password = '';
  error    = '';
  loading  = false;
  showPwd  = false;

  // Face recognition
  faceRecognitionEnabled = false;
  showFaceModal = false;
  faceLoading = false;
  faceError = '';
  faceSuccess = '';
  cameraActive = false;
  enrollMode = false;
  verifyMode = false;
  detectedFace = false;
  faceConfidence = 0;
  timeoutCountdown = 15; // Countdown timer
  loginMethod: 'password' | 'face' = 'password'; // Login method toggle
  isDarkMode = true; // Theme toggle (default: dark)

  private videoStream: MediaStream | null = null;
  private detectionInterval: any = null;
  private verificationTimeout: any = null;
  private countdownInterval: any = null;
  private readonly VERIFICATION_TIMEOUT_MS = 15000; // 15 seconds

  constructor(
    private auth: AuthService,
    private router: Router,
    private faceService: FaceRecognitionService,
    private themeService: ThemeService,
    public translate: TranslationService
  ) {
    if (this.auth.isLoggedIn()) {
      this.router.navigate([this.auth.getDefaultPage()]);
    }
  }

  ngOnInit() {
    // Check if face recognition is available
    this.faceRecognitionEnabled = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    
    // Initialize theme from service
    this.isDarkMode = this.themeService.getCurrentTheme();
    
    // Subscribe to theme changes
    this.themeService.isDarkMode$.subscribe(isDark => {
      this.isDarkMode = isDark;
      console.log('Login page theme changed to:', isDark ? 'dark' : 'light');
    });
    
    // Check if user has registered face and set default login method
    const lastUsername = localStorage.getItem('last_username');
    if (lastUsername) {
      this.username = lastUsername;
      const hasFace = this.faceService.getFaceDescriptor(lastUsername);
      if (hasFace && this.faceRecognitionEnabled) {
        this.loginMethod = 'face'; // Default to Face ID if registered
      }
    }
  }

  ngOnDestroy() {
    this.stopCamera();
    this.clearVerificationTimeout();
  }

  login() {
    if (!this.username || !this.password) {
      this.error = this.translate.translate('login.errors.enterCredentials');
      return;
    }
    this.loading = true;
    this.error   = '';

    setTimeout(() => {
      const ok = this.auth.login(this.username, this.password);
      if (ok) {
        // Store last username for next login
        localStorage.setItem('last_username', this.username);
        this.router.navigate([this.auth.getDefaultPage()]);
      } else {
        this.error   = this.translate.translate('login.errors.invalidCredentials');
        this.loading = false;
      }
    }, 400);
  }

  onKey(e: KeyboardEvent) {
    if (e.key === 'Enter') this.login();
  }

  /**
   * Toggle between dark and light theme
   */
  toggleTheme() {
    this.themeService.toggleTheme();
  }

  /**
   * Switch between password and face ID login methods
   */
  switchLoginMethod(method: 'password' | 'face') {
    this.loginMethod = method;
    this.error = '';
    
    // Check if face is registered when switching to face ID
    if (method === 'face' && this.username) {
      const hasFace = this.faceService.getFaceDescriptor(this.username);
      if (!hasFace) {
        this.error = this.translate.translate('login.errors.noFaceRegistered');
        this.loginMethod = 'password';
      }
    }
  }

  /**
   * Open face recognition modal for LOGIN (verification only)
   */
  openFaceModal() {
    if (!this.username) {
      this.error = this.translate.translate('login.errors.enterCredentials');
      return;
    }

    // SECURITY: Check if user has enrolled face
    const hasFace = this.faceService.getFaceDescriptor(this.username);
    if (!hasFace) {
      this.error = this.translate.translate('login.errors.noFaceRegistered');
      return;
    }

    this.showFaceModal = true;
    this.faceError = '';
    this.faceSuccess = '';
    this.verifyMode = true;
    this.enrollMode = false;

    setTimeout(() => this.startCamera(), 100);
  }

  /**
   * Open face enrollment modal (only after password login)
   */
  openEnrollModal() {
    if (!this.username || !this.password) {
      this.error = this.translate.translate('login.errors.enterCredentials');
      return;
    }

    // SECURITY: Verify password before allowing enrollment
    const isValidUser = this.auth.validateCredentials(this.username, this.password);
    if (!isValidUser) {
      this.error = this.translate.translate('login.errors.invalidCredentials');
      return;
    }

    this.showFaceModal = true;
    this.faceError = '';
    this.faceSuccess = '';
    this.enrollMode = true;
    this.verifyMode = false;

    setTimeout(() => this.startCamera(), 100);
  }

  /**
   * Start camera for face detection
   */
  async startCamera() {
    try {
      this.faceLoading = true;
      this.faceError = '';

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240 }
      });

      this.videoStream = stream;
      const video = this.videoElement.nativeElement;
      video.srcObject = stream;

      // Wait for video to load
      await new Promise(resolve => {
        video.onloadedmetadata = () => {
          video.play();
          resolve(null);
        };
      });

      this.cameraActive = true;
      this.faceLoading = false;

      // Start face detection loop
      this.startFaceDetection();

      // Start 15-second timeout for verification mode
      if (this.verifyMode) {
        this.startVerificationTimeout();
      }
    } catch (error: any) {
      this.faceError = `Camera error: ${error.message}`;
      this.faceLoading = false;
      console.error('Camera error:', error);
    }
  }

  /**
   * Start continuous face detection
   */
  private startFaceDetection() {
    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
    }

    this.detectionInterval = setInterval(async () => {
      const video = this.videoElement?.nativeElement;
      if (!video || !this.cameraActive) return;

      try {
        const detection = await this.faceService.detectFaceInVideo(video);

        if (detection) {
          this.detectedFace = true;
          this.faceConfidence = Math.round((1 - detection.detection.score) * 100);

          if (this.enrollMode) {
            // Enrollment mode: store face after 2 seconds of detection
            setTimeout(() => {
              if (this.detectedFace && detection) {
                this.enrollFace(detection.descriptor);
              }
            }, 2000);
          } else if (this.verifyMode) {
            // Verification mode: verify face
            this.verifyFace(detection.descriptor);
          }
        } else {
          this.detectedFace = false;
          this.faceConfidence = 0;
        }
      } catch (error) {
        console.error('Detection error:', error);
      }
    }, 500);
  }

  /**
   * Enroll face for current user (only after password verification)
   */
  private enrollFace(descriptor: Float32Array) {
    // SECURITY: Double-check password before storing face
    const isValidUser = this.auth.validateCredentials(this.username, this.password);
    if (!isValidUser) {
      this.faceError = 'Invalid credentials. Cannot enroll face.';
      this.stopCamera();
      return;
    }

    // Store face descriptor
    this.faceService.storeFaceDescriptor(this.username, descriptor);
    
    // Store password for future face login
    this.auth.storePasswordForFaceLogin(this.username, this.password);
    
    this.faceSuccess = '✓ Face registered successfully! You can now use Face ID to login.';
    this.enrollMode = false;
    this.faceError = '';

    setTimeout(() => {
      this.closeFaceModal();
      this.faceSuccess = '';
    }, 2000);
  }

  /**
   * Verify face for login
   */
  private verifyFace(descriptor: Float32Array) {
    const isMatch = this.faceService.verifyFace(descriptor, this.username, 0.6);

    if (isMatch) {
      // Clear timeout on successful verification
      this.clearVerificationTimeout();
      
      this.faceSuccess = '✓ Face verified! Logging in...';
      this.stopCamera();
      this.closeFaceModal();

      // SECURITY: Get stored password and login
      setTimeout(() => {
        const storedPassword = this.auth.getStoredPassword(this.username);
        if (storedPassword) {
          this.password = storedPassword;
          this.login();
        } else {
          this.error = 'Face verified but password not found. Please login with password.';
        }
      }, 500);
    }
  }

  /**
   * Start 15-second verification timeout
   */
  private startVerificationTimeout() {
    this.clearVerificationTimeout();
    
    // Reset countdown
    this.timeoutCountdown = 15;
    
    // Start countdown timer (updates every second)
    this.countdownInterval = setInterval(() => {
      this.timeoutCountdown--;
      if (this.timeoutCountdown <= 0) {
        clearInterval(this.countdownInterval);
      }
    }, 1000);
    
    // Start timeout
    this.verificationTimeout = setTimeout(() => {
      if (this.verifyMode && this.cameraActive) {
        this.faceError = '⏱️ Timeout: Face not recognized within 15 seconds. Please try again or use password login.';
        this.stopCamera();
        
        // Auto-close modal after 3 seconds
        setTimeout(() => {
          if (this.showFaceModal) {
            this.closeFaceModal();
          }
        }, 3000);
      }
    }, this.VERIFICATION_TIMEOUT_MS);
  }

  /**
   * Clear verification timeout
   */
  private clearVerificationTimeout() {
    if (this.verificationTimeout) {
      clearTimeout(this.verificationTimeout);
      this.verificationTimeout = null;
    }
    
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    
    this.timeoutCountdown = 15;
  }

  /**
   * Stop camera
   */
  stopCamera() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach(track => track.stop());
      this.videoStream = null;
    }

    if (this.detectionInterval) {
      clearInterval(this.detectionInterval);
      this.detectionInterval = null;
    }

    this.clearVerificationTimeout();

    this.cameraActive = false;
    this.detectedFace = false;
  }

  /**
   * Close face modal
   */
  closeFaceModal() {
    this.showFaceModal = false;
    this.stopCamera();
    this.clearVerificationTimeout();
    this.faceError = '';
    this.faceSuccess = '';
  }

  /**
   * Clear enrolled face
   */
  clearEnrolledFace() {
    if (confirm(`Clear enrolled face for ${this.username}?`)) {
      this.faceService.clearUserFace(this.username);
      this.faceError = 'Face cleared. Please enroll again.';
      this.enrollMode = true;
      this.verifyMode = false;
    }
  }
}
