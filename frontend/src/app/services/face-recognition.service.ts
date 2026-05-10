import { Injectable } from '@angular/core';

declare global {
  interface Window {
    faceapi: any;
  }
}

@Injectable({
  providedIn: 'root'
})
export class FaceRecognitionService {
  private modelsLoaded = false;
  private readonly MODELS_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/';
  private storedFaceDescriptors: Map<string, Float32Array> = new Map();

  constructor() {
    this.loadFaceApiScript();
  }

  /**
   * Load face-api.js from CDN
   */
  private loadFaceApiScript(): void {
    if (window.faceapi) {
      this.loadModels();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.js';
    script.async = true;
    script.onload = () => {
      console.log('✓ Face API script loaded from CDN');
      this.loadModels();
    };
    script.onerror = () => {
      console.error('✗ Failed to load face-api.js from CDN');
    };
    document.head.appendChild(script);
  }

  /**
   * Load face-api models from CDN
   */
  async loadModels(): Promise<void> {
    if (this.modelsLoaded || !window.faceapi) return;

    try {
      const faceapi = window.faceapi;
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(this.MODELS_URL),
        faceapi.nets.faceLandmark68Net.loadFromUri(this.MODELS_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(this.MODELS_URL),
        faceapi.nets.faceExpressionNet.loadFromUri(this.MODELS_URL),
      ]);
      this.modelsLoaded = true;
      console.log('✓ Face API models loaded successfully');
    } catch (error) {
      console.error('✗ Failed to load face API models:', error);
      throw new Error('Failed to load face recognition models');
    }
  }

  /**
   * Detect faces in a video stream
   */
  async detectFaceInVideo(videoElement: HTMLVideoElement): Promise<any> {
    if (!this.modelsLoaded || !window.faceapi) {
      await this.loadModels();
    }

    try {
      const faceapi = window.faceapi;
      const detection = await faceapi
        .detectSingleFace(videoElement, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceDescriptor();

      return detection || null;
    } catch (error) {
      console.error('Error detecting face:', error);
      return null;
    }
  }

  /**
   * Detect faces in an image
   */
  async detectFaceInImage(imageElement: HTMLImageElement): Promise<any> {
    if (!this.modelsLoaded || !window.faceapi) {
      await this.loadModels();
    }

    try {
      const faceapi = window.faceapi;
      const detection = await faceapi
        .detectSingleFace(imageElement, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceDescriptor();

      return detection || null;
    } catch (error) {
      console.error('Error detecting face in image:', error);
      return null;
    }
  }

  /**
   * Store face descriptor for a user (enrollment)
   */
  storeFaceDescriptor(username: string, descriptor: Float32Array): void {
    this.storedFaceDescriptors.set(username, descriptor);
    // In production, save to backend/database
    localStorage.setItem(`face_${username}`, JSON.stringify(Array.from(descriptor)));
    console.log(`✓ Face stored for user: ${username}`);
  }

  /**
   * Retrieve stored face descriptor for a user
   */
  getFaceDescriptor(username: string): Float32Array | null {
    // Try to get from memory first
    if (this.storedFaceDescriptors.has(username)) {
      return this.storedFaceDescriptors.get(username) || null;
    }

    // Try to get from localStorage
    const stored = localStorage.getItem(`face_${username}`);
    if (stored) {
      try {
        const descriptor = new Float32Array(JSON.parse(stored));
        this.storedFaceDescriptors.set(username, descriptor);
        return descriptor;
      } catch (error) {
        console.error('Error parsing stored face descriptor:', error);
        return null;
      }
    }

    return null;
  }

  /**
   * Compare two face descriptors
   * Returns distance (lower = more similar, 0.6 is typical threshold)
   */
  compareFaces(descriptor1: Float32Array, descriptor2: Float32Array): number {
    if (descriptor1.length !== descriptor2.length) {
      throw new Error('Descriptors must have the same length');
    }

    let sum = 0;
    for (let i = 0; i < descriptor1.length; i++) {
      const diff = descriptor1[i] - descriptor2[i];
      sum += diff * diff;
    }

    return Math.sqrt(sum);
  }

  /**
   * Verify if a detected face matches a stored face
   * Returns true if distance is below threshold
   */
  verifyFace(detectedDescriptor: Float32Array, username: string, threshold: number = 0.6): boolean {
    const storedDescriptor = this.getFaceDescriptor(username);
    if (!storedDescriptor) {
      console.warn(`No stored face found for user: ${username}`);
      return false;
    }

    const distance = this.compareFaces(detectedDescriptor, storedDescriptor);
    console.log(`Face comparison distance: ${distance.toFixed(4)} (threshold: ${threshold})`);

    return distance < threshold;
  }

  /**
   * Clear all stored face descriptors
   */
  clearAllFaces(): void {
    this.storedFaceDescriptors.clear();
    // Clear localStorage
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('face_')) {
        localStorage.removeItem(key);
      }
    });
    console.log('✓ All face descriptors cleared');
  }

  /**
   * Clear face descriptor for a specific user
   */
  clearUserFace(username: string): void {
    this.storedFaceDescriptors.delete(username);
    localStorage.removeItem(`face_${username}`);
    console.log(`✓ Face cleared for user: ${username}`);
  }

  /**
   * Check if models are loaded
   */
  isModelsLoaded(): boolean {
    return this.modelsLoaded;
  }
}
