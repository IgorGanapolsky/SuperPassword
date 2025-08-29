import {
  collection,
  doc,
  getDocs,
  setDoc,
  query,
  where,
  orderBy,
  limit,
} from "firebase/firestore";
import { auth, db } from "../config/firebase";
import { StorageService } from "./storage";
import { premiumService } from "./premium";
import { encrypt, decrypt } from "../utils/encryption";
import { PasswordEntry, UserPreferences } from "../types";

class SyncService {
  private static instance: SyncService;
  private syncInProgress = false;
  private lastSyncTimestamp: number = 0;
  private encryptionKey: string | null = null;

  private constructor() {}

  static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }

  async initialize(): Promise<void> {
    // Listen for auth state changes
    auth.onAuthStateChanged(async (user) => {
      if (user) {
        // Generate encryption key from user's UID and a server-side salt
        this.encryptionKey = await this.generateEncryptionKey(user.uid);
        await this.syncOnLogin();
      } else {
        this.encryptionKey = null;
      }
    });
  }

  private async generateEncryptionKey(uid: string): Promise<string> {
    // In production, this would use a more sophisticated key derivation
    // possibly involving a server-side component for added security
    return uid + "_encryption_key";
  }

  async syncOnLogin(): Promise<void> {
    if (!premiumService.hasFeature("cloud_sync")) return;

    const user = auth.currentUser;
    if (!user || this.syncInProgress) return;

    try {
      this.syncInProgress = true;

      // Get last sync timestamp from Firestore
      const userDoc = await getDocs(
        collection(db, `users/${user.uid}/metadata`),
      );
      const serverLastSync = userDoc.docs[0]?.data()?.lastSync || 0;

      if (serverLastSync > this.lastSyncTimestamp) {
        // Server has newer data
        await this.pullFromCloud();
      } else if (this.lastSyncTimestamp > serverLastSync) {
        // Local has newer data
        await this.pushToCloud();
      }

      this.lastSyncTimestamp = Date.now();
      await setDoc(doc(db, `users/${user.uid}/metadata`, "sync"), {
        lastSync: this.lastSyncTimestamp,
      });
    } finally {
      this.syncInProgress = false;
    }
  }

  private async pullFromCloud(): Promise<void> {
    const user = auth.currentUser;
    if (!user || !this.encryptionKey) return;

    // Fetch passwords
    const passwordsRef = collection(db, `users/${user.uid}/passwords`);
    const q = query(passwordsRef, orderBy("timestamp", "desc"), limit(1000));
    const snapshot = await getDocs(q);

    const passwords: PasswordEntry[] = [];
    snapshot.forEach((doc) => {
      const data = doc.data();
      passwords.push({
        ...data,
        password: decrypt(data.password, this.encryptionKey!),
        timestamp: data.timestamp.toDate(),
      } as PasswordEntry);
    });

    // Fetch preferences
    const prefsDoc = await getDocs(
      collection(db, `users/${user.uid}/preferences`),
    );
    const preferences = prefsDoc.docs[0]?.data() as UserPreferences;

    // Update local storage
    await StorageService.savePasswordHistory(passwords);
    if (preferences) {
      await StorageService.saveUserPreferences(preferences);
    }
  }

  private async pushToCloud(): Promise<void> {
    const user = auth.currentUser;
    if (!user || !this.encryptionKey) return;

    // Push passwords
    const passwords = await StorageService.getPasswordHistory();
    for (const password of passwords) {
      const encryptedPassword = encrypt(password.password, this.encryptionKey);
      await setDoc(doc(db, `users/${user.uid}/passwords`, password.id), {
        ...password,
        password: encryptedPassword,
      });
    }

    // Push preferences
    const preferences = await StorageService.getUserPreferences();
    if (preferences) {
      await setDoc(
        doc(db, `users/${user.uid}/preferences`, "current"),
        preferences,
      );
    }
  }

  async forceSyncToCloud(): Promise<void> {
    if (!premiumService.hasFeature("cloud_sync")) {
      throw new Error("Cloud sync is a premium feature");
    }

    const user = auth.currentUser;
    if (!user) {
      throw new Error("User must be logged in to sync");
    }

    if (this.syncInProgress) {
      throw new Error("Sync already in progress");
    }

    try {
      this.syncInProgress = true;
      await this.pushToCloud();
      this.lastSyncTimestamp = Date.now();
    } finally {
      this.syncInProgress = false;
    }
  }
}

export const syncService = SyncService.getInstance();
