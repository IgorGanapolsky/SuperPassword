import CryptoJS from 'crypto-js';
import * as Crypto from 'expo-crypto';
import * as SecureStore from 'expo-secure-store';

/**
 * SecureStorageService provides encrypted storage for sensitive data
 * using AES-256 encryption and device secure storage
 */
export class SecureStorageService {
  private static readonly ENCRYPTION_KEY_NAME = 'SP_MASTER_KEY';
  private static readonly KEY_SIZE = 256;
  
  /**
   * Generate or retrieve the master encryption key
   */
  private static async getMasterKey(): Promise<string> {
    try {
      // Try to get existing key
      let masterKey = await SecureStore.getItemAsync(this.ENCRYPTION_KEY_NAME);
      
      if (!masterKey) {
        // Generate new master key if not exists
        const randomBytes = await Crypto.getRandomBytesAsync(32);
        masterKey = btoa(String.fromCharCode(...new Uint8Array(randomBytes)));
        await SecureStore.setItemAsync(this.ENCRYPTION_KEY_NAME, masterKey);
      }
      
      return masterKey;
    } catch (error) {
      console.error('Failed to get/generate master key:', error);
      throw new Error('Encryption key management failed');
    }
  }

  /**
   * Encrypt data using AES-256
   */
  static async encryptData(data: string): Promise<string> {
    try {
      const masterKey = await this.getMasterKey();
      const encrypted = CryptoJS.AES.encrypt(data, masterKey, {
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7,
      });
      return encrypted.toString();
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Data encryption failed');
    }
  }

  /**
   * Decrypt data using AES-256
   */
  static async decryptData(encryptedData: string): Promise<string> {
    try {
      const masterKey = await this.getMasterKey();
      const decrypted = CryptoJS.AES.decrypt(encryptedData, masterKey, {
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7,
      });
      return decrypted.toString(CryptoJS.enc.Utf8);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Data decryption failed');
    }
  }

  /**
   * Store data securely with encryption
   */
  static async secureStore(key: string, value: any): Promise<void> {
    try {
      const jsonString = JSON.stringify(value);
      const encrypted = await this.encryptData(jsonString);
      
      // Store encrypted data
      await SecureStore.setItemAsync(key, encrypted, {
        keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
      });
    } catch (error) {
      console.error('Secure storage failed:', error);
      throw new Error('Failed to store data securely');
    }
  }

  /**
   * Retrieve and decrypt data from secure storage
   */
  static async secureRetrieve<T = any>(key: string): Promise<T | null> {
    try {
      const encrypted = await SecureStore.getItemAsync(key);
      if (!encrypted) return null;
      
      const decrypted = await this.decryptData(encrypted);
      return JSON.parse(decrypted) as T;
    } catch (error) {
      console.error('Secure retrieval failed:', error);
      return null;
    }
  }

  /**
   * Remove data from secure storage
   */
  static async secureRemove(key: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      console.error('Secure removal failed:', error);
      throw new Error('Failed to remove data securely');
    }
  }

  /**
   * Check if secure storage is available on the device
   */
  static async isAvailable(): Promise<boolean> {
    try {
      // Test write and read
      const testKey = 'SP_TEST_KEY';
      const testValue = 'test';
      await SecureStore.setItemAsync(testKey, testValue);
      const retrieved = await SecureStore.getItemAsync(testKey);
      await SecureStore.deleteItemAsync(testKey);
      return retrieved === testValue;
    } catch {
      return false;
    }
  }

  /**
   * Clear all secure storage (use with caution)
   */
  static async clearAll(): Promise<void> {
    // Note: SecureStore doesn't provide a clear all method
    // You need to track keys and delete them individually
    const keys = [
      'passwordHistory',
      'userPreferences', 
      'userData',
      'premiumStatus',
      this.ENCRYPTION_KEY_NAME,
    ];
    
    for (const key of keys) {
      try {
        await SecureStore.deleteItemAsync(key);
      } catch {
        // Key might not exist, continue
      }
    }
  }
}
