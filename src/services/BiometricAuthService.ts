import * as LocalAuthentication from 'expo-local-authentication';
import { Platform } from 'react-native';

export enum BiometricType {
  FINGERPRINT = 'fingerprint',
  FACIAL_RECOGNITION = 'facial_recognition',
  IRIS = 'iris',
  NONE = 'none',
}

export interface BiometricAuthResult {
  success: boolean;
  error?: string;
  warning?: string;
}

/**
 * BiometricAuthService handles device biometric authentication
 * including FaceID, TouchID, and fingerprint authentication
 */
export class BiometricAuthService {
  private static isAuthenticating = false;
  private static lastAuthTime: Date | null = null;
  private static readonly AUTH_VALIDITY_DURATION = 5 * 60 * 1000; // 5 minutes

  /**
   * Check if biometric hardware is available
   */
  static async isAvailable(): Promise<boolean> {
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = await LocalAuthentication.isEnrolledAsync();
      return hasHardware && isEnrolled;
    } catch {
      return false;
    }
  }

  /**
   * Get available biometric types on the device
   */
  static async getAvailableTypes(): Promise<BiometricType[]> {
    try {
      const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
      const biometricTypes: BiometricType[] = [];

      types.forEach(type => {
        switch (type) {
          case LocalAuthentication.AuthenticationType.FINGERPRINT:
            biometricTypes.push(BiometricType.FINGERPRINT);
            break;
          case LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION:
            biometricTypes.push(BiometricType.FACIAL_RECOGNITION);
            break;
          case LocalAuthentication.AuthenticationType.IRIS:
            biometricTypes.push(BiometricType.IRIS);
            break;
        }
      });

      return biometricTypes.length > 0 ? biometricTypes : [BiometricType.NONE];
    } catch {
      return [BiometricType.NONE];
    }
  }

  /**
   * Authenticate using biometrics
   */
  static async authenticate(
    promptMessage?: string,
    fallbackLabel?: string,
  ): Promise<BiometricAuthResult> {
    // Prevent multiple simultaneous authentication attempts
    if (this.isAuthenticating) {
      return {
        success: false,
        error: 'Authentication already in progress',
      };
    }

    // Check if recently authenticated
    if (this.isRecentlyAuthenticated()) {
      return { success: true };
    }

    this.isAuthenticating = true;

    try {
      // Check availability first
      const isAvailable = await this.isAvailable();
      if (!isAvailable) {
        return {
          success: false,
          error: 'Biometric authentication not available',
          warning: 'Please enable biometric authentication in device settings',
        };
      }

      // Perform authentication
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: promptMessage || 'Authenticate to access your passwords',
        fallbackLabel: fallbackLabel || Platform.OS === 'ios' ? 'Use Passcode' : 'Use PIN',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
        requireConfirmation: Platform.OS === 'android',
      });

      if (result.success) {
        this.lastAuthTime = new Date();
        return { success: true };
      }

      // Handle different error cases
      let errorMessage = 'Authentication failed';
      let warning: string | undefined;

      const error = result.error as string;
      switch (error) {
        case 'UserCancel':
          errorMessage = 'Authentication cancelled';
          break;
        case 'UserFallback':
          errorMessage = 'Please use passcode/PIN';
          break;
        case 'SystemCancel':
          errorMessage = 'Authentication interrupted';
          break;
        case 'PasscodeNotSet':
          errorMessage = 'Device passcode not set';
          warning = 'Please set a device passcode to use this feature';
          break;
        case 'BiometryNotAvailable':
          errorMessage = 'Biometric authentication not available';
          break;
        case 'BiometryNotEnrolled':
          errorMessage = 'No biometrics enrolled';
          warning = 'Please enroll biometrics in device settings';
          break;
        case 'BiometryLockout':
          errorMessage = 'Too many failed attempts';
          warning = 'Biometric authentication is temporarily disabled';
          break;
        default:
          errorMessage = error || 'Unknown authentication error';
      }

      return {
        success: false,
        error: errorMessage,
        warning,
      };
    } catch (error) {
      console.error('Biometric authentication error:', error);
      return {
        success: false,
        error: 'Authentication system error',
      };
    } finally {
      this.isAuthenticating = false;
    }
  }

  /**
   * Require authentication before proceeding
   */
  static async requireAuthentication(
    promptMessage?: string,
  ): Promise<void> {
    const result = await this.authenticate(promptMessage);
    
    if (!result.success) {
      const errorMessage = result.warning 
        ? `${result.error}\n\n${result.warning}`
        : result.error;
      throw new Error(errorMessage || 'Authentication required');
    }
  }

  /**
   * Check if user was recently authenticated
   */
  static isRecentlyAuthenticated(): boolean {
    if (!this.lastAuthTime) return false;
    
    const now = new Date();
    const timeDiff = now.getTime() - this.lastAuthTime.getTime();
    return timeDiff < this.AUTH_VALIDITY_DURATION;
  }

  /**
   * Clear authentication session
   */
  static clearSession(): void {
    this.lastAuthTime = null;
  }

  /**
   * Get security level description for UI
   */
  static async getSecurityLevel(): Promise<string> {
    const types = await this.getAvailableTypes();
    
    if (types.includes(BiometricType.FACIAL_RECOGNITION)) {
      return Platform.OS === 'ios' ? 'Face ID' : 'Face Recognition';
    }
    if (types.includes(BiometricType.FINGERPRINT)) {
      return Platform.OS === 'ios' ? 'Touch ID' : 'Fingerprint';
    }
    if (types.includes(BiometricType.IRIS)) {
      return 'Iris Recognition';
    }
    
    return 'Passcode/PIN';
  }

  /**
   * Check if the app should prompt for authentication
   */
  static async shouldPromptForAuth(): Promise<boolean> {
    // Check if biometrics are available
    const isAvailable = await this.isAvailable();
    if (!isAvailable) return false;

    // Check if not recently authenticated
    return !this.isRecentlyAuthenticated();
  }
}
