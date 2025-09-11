import admin from 'firebase-admin';

export class FirebaseService {
  private app: admin.app.App;

  constructor() {
    // Initialize Firebase Admin SDK
    if (!admin.apps.length) {
      try {
        const serviceAccount = {
          projectId: process.env.FIREBASE_PROJECT_ID,
          privateKeyId: process.env.FIREBASE_PRIVATE_KEY_ID,
          privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
          clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
          clientId: process.env.FIREBASE_CLIENT_ID,
          authUri: process.env.FIREBASE_AUTH_URI,
          tokenUri: process.env.FIREBASE_TOKEN_URI,
        };

        this.app = admin.initializeApp({
          credential: admin.credential.cert(serviceAccount as admin.ServiceAccount),
          projectId: process.env.FIREBASE_PROJECT_ID,
        });
      } catch (error) {
        console.warn('Firebase Admin not configured, using mock authentication for development');
        // Create mock app for development
        this.app = null as any;
      }
    } else {
      this.app = admin.apps[0]!;
    }
  }

  async verifyToken(token: string): Promise<admin.auth.DecodedIdToken> {
    if (!this.app || process.env.NODE_ENV === 'development') {
      // Mock authentication for development
      return {
        uid: 'dev-user-123',
        email: 'developer@superpassword.app',
        email_verified: true,
        firebase: {
          identities: {},
          sign_in_provider: 'mock'
        },
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600,
        aud: 'mock-project',
        iss: 'https://securetoken.google.com/mock-project',
        sub: 'dev-user-123',
        auth_time: Math.floor(Date.now() / 1000)
      } as admin.auth.DecodedIdToken;
    }

    try {
      const decodedToken = await admin.auth().verifyIdToken(token);
      return decodedToken;
    } catch (error) {
      throw new Error(`Invalid token: ${error}`);
    }
  }

  async getUserProfile(uid: string): Promise<any> {
    if (!this.app || process.env.NODE_ENV === 'development') {
      // Mock user profile for development
      return {
        uid: 'dev-user-123',
        email: 'developer@superpassword.app',
        displayName: 'Development User',
        tier: 'pro',
        createdAt: new Date().toISOString(),
        lastLogin: new Date().toISOString()
      };
    }

    try {
      const userRecord = await admin.auth().getUser(uid);
      return {
        uid: userRecord.uid,
        email: userRecord.email,
        displayName: userRecord.displayName,
        createdAt: userRecord.metadata.creationTime,
        lastLogin: userRecord.metadata.lastSignInTime,
      };
    } catch (error) {
      throw new Error(`User not found: ${error}`);
    }
  }

  async createUser(email: string, password: string, displayName?: string): Promise<admin.auth.UserRecord> {
    if (!this.app) {
      throw new Error('Firebase not configured');
    }

    return admin.auth().createUser({
      email,
      password,
      displayName,
      emailVerified: false,
    });
  }

  async updateUser(uid: string, updates: admin.auth.UpdateRequest): Promise<admin.auth.UserRecord> {
    if (!this.app) {
      throw new Error('Firebase not configured');
    }

    return admin.auth().updateUser(uid, updates);
  }

  async deleteUser(uid: string): Promise<void> {
    if (!this.app) {
      throw new Error('Firebase not configured');
    }

    await admin.auth().deleteUser(uid);
  }

  async setCustomClaims(uid: string, customClaims: object): Promise<void> {
    if (!this.app) {
      throw new Error('Firebase not configured');
    }

    await admin.auth().setCustomUserClaims(uid, customClaims);
  }

  // Firestore operations
  getFirestore(): admin.firestore.Firestore | null {
    if (!this.app) {
      return null;
    }
    return admin.firestore();
  }

  async saveUserData(uid: string, data: any): Promise<void> {
    const firestore = this.getFirestore();
    if (!firestore) {
      console.log('Mock: Saving user data for', uid, data);
      return;
    }

    await firestore.collection('users').doc(uid).set(data, { merge: true });
  }

  async getUserData(uid: string): Promise<any> {
    const firestore = this.getFirestore();
    if (!firestore) {
      // Mock user data for development
      return {
        tier: 'pro',
        preferences: {
          analysisDepth: 'comprehensive',
          reportFormat: 'user-friendly',
          notificationFrequency: 'weekly'
        },
        limits: {
          maxPasswordsPerAudit: 1000,
          auditsPerMonth: 50,
          phishingChecksPerDay: 100
        },
        features: ['vault_audit', 'breach_detection', 'phishing_protection', 'rotation_planning']
      };
    }

    const doc = await firestore.collection('users').doc(uid).get();
    return doc.exists ? doc.data() : null;
  }

  async saveAuditResult(uid: string, auditResult: any): Promise<string> {
    const firestore = this.getFirestore();
    if (!firestore) {
      console.log('Mock: Saving audit result for', uid);
      return `mock-audit-${Date.now()}`;
    }

    const docRef = await firestore.collection('audits').add({
      userId: uid,
      timestamp: new Date().toISOString(),
      ...auditResult
    });

    return docRef.id;
  }

  async getAuditHistory(uid: string, limit = 10): Promise<any[]> {
    const firestore = this.getFirestore();
    if (!firestore) {
      // Mock audit history for development
      return [
        {
          id: 'mock-audit-1',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          securityScore: 75,
          totalPasswords: 45,
          weakPasswordCount: 8,
          breachedPasswordCount: 2
        },
        {
          id: 'mock-audit-2',
          timestamp: new Date(Date.now() - 86400000 * 7).toISOString(),
          securityScore: 70,
          totalPasswords: 42,
          weakPasswordCount: 12,
          breachedPasswordCount: 3
        }
      ];
    }

    const snapshot = await firestore
      .collection('audits')
      .where('userId', '==', uid)
      .orderBy('timestamp', 'desc')
      .limit(limit)
      .get();

    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  }
}
