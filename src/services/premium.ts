import { doc, getDoc, setDoc } from "firebase/firestore";
import { getFunctions, httpsCallable } from "firebase/functions";
import { auth, db } from "../config/firebase";

export type Subscription = {
  status: "active" | "canceled" | "expired";
  type: "monthly" | "yearly" | "lifetime";
  startDate: Date;
  endDate?: Date;
  features: string[];
};

export type PremiumFeature =
  | "cloud_sync"
  | "unlimited_history"
  | "advanced_generator"
  | "password_analyzer"
  | "priority_support";

class PremiumService {
  private static instance: PremiumService;
  private subscription: Subscription | null = null;
  private features: Set<PremiumFeature> = new Set();

  private constructor() {}

  static getInstance(): PremiumService {
    if (!PremiumService.instance) {
      PremiumService.instance = new PremiumService();
    }
    return PremiumService.instance;
  }

  async initialize(): Promise<void> {
    await this.loadSubscription();
  }

  async loadSubscription(): Promise<void> {
    const user = auth.currentUser;
    if (!user) return;

    const docRef = doc(db, "subscriptions", user.uid);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      const data = docSnap.data();
      this.subscription = {
        ...data,
        startDate: data.startDate.toDate(),
        endDate: data.endDate?.toDate(),
      };
      this.updateFeatures();
    }
  }

  private updateFeatures(): void {
    this.features.clear();

    if (!this.subscription || this.subscription.status !== "active") {
      return;
    }

    this.features = new Set(this.subscription.features as PremiumFeature[]);
  }

  async purchaseSubscription(type: "monthly" | "yearly"): Promise<void> {
    const functions = getFunctions();
    const createSubscription = httpsCallable<
      { type: "monthly" | "yearly" },
      { sessionUrl: string }
    >(functions, "createSubscription");

    const result = await createSubscription({ type });

    // Redirect to Stripe Checkout
    if (typeof window !== "undefined") {
      window.location.href = result.data.sessionUrl;
    }
  }

  async cancelSubscription(): Promise<void> {
    const functions = getFunctions();
    const cancelSub = httpsCallable(functions, "cancelSubscription");
    await cancelSub();
    await this.loadSubscription();
  }

  hasFeature(feature: PremiumFeature): boolean {
    return this.features.has(feature);
  }

  isSubscriptionActive(): boolean {
    return this.subscription?.status === "active";
  }

  getSubscriptionDetails(): Subscription | null {
    return this.subscription;
  }
}

export const premiumService = PremiumService.getInstance();
