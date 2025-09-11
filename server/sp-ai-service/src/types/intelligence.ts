// Request/Response types for AI Intelligence API

export interface PasswordEntry {
  id?: string;
  site: string;
  username: string;
  password: string;
  lastUpdated?: string;
  category?: string;
  notes?: string;
}

export interface VaultAuditRequest {
  requestId: string;
  userId: string;
  passwords: PasswordEntry[];
  analysisDepth?: 'basic' | 'standard' | 'comprehensive';
  includeBreachCheck?: boolean;
  includeTrendAnalysis?: boolean;
}

export interface VaultAuditResult {
  requestId: string;
  userId: string;
  timestamp: string;
  securityScore: number;
  riskLevel: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  
  // Vulnerability categories
  weakPasswords: WeakPasswordInfo[];
  breachedPasswords: BreachedPasswordInfo[];
  duplicatePasswords: DuplicatePasswordGroup[];
  stalePasswords: StalePasswordInfo[];
  
  // Analysis results
  recommendations: string[];
  summary: string;
  keyMetrics: SecurityMetrics;
  priorityActions: string[];
  nextReviewDate: string;
  
  // Optional detailed analysis
  trendAnalysis?: TrendAnalysis;
  complianceStatus?: ComplianceStatus;
}

export interface WeakPasswordInfo {
  entryId: string;
  site: string;
  weaknessReasons: string[];
  currentStrength: number; // 0-100
  recommendedActions: string[];
  estimatedFixTime: number; // minutes
}

export interface BreachedPasswordInfo {
  entryId: string;
  site: string;
  breachCount: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  firstSeen?: string;
  sources: string[];
  recommendation: string;
}

export interface DuplicatePasswordGroup {
  passwordHash: string; // truncated hash for identification
  entryIds: string[];
  sites: string[];
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendation: string;
}

export interface StalePasswordInfo {
  entryId: string;
  site: string;
  lastUpdated: string;
  daysSinceUpdate: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  recommendation: string;
}

export interface SecurityMetrics {
  totalPasswords: number;
  securityScore: number;
  weakPasswordCount: number;
  breachedPasswordCount: number;
  duplicatePasswordCount: number;
  stalePasswordCount: number;
  averagePasswordAge: number;
  strongPasswordsPercentage: number;
  criticalIssueCount: number;
  lastAuditDate: string;
}

export interface TrendAnalysis {
  scoreHistory: ScoreDataPoint[];
  improvementTrend: 'improving' | 'stable' | 'declining';
  periodOverPeriodChange: number;
  projectedScore: number;
  recommendedActions: string[];
}

export interface ScoreDataPoint {
  date: string;
  score: number;
  issueCount: number;
}

export interface ComplianceStatus {
  gdprCompliant: boolean;
  ccpaCompliant: boolean;
  hipaaCompliant?: boolean;
  soc2Compliant?: boolean;
  issues: string[];
  recommendations: string[];
}

// Phishing Check Types
export interface PhishingCheckRequest {
  requestId: string;
  url: string;
  context?: string;
  userAgent?: string;
  referrer?: string;
}

export interface PhishingCheckResult {
  requestId: string;
  url: string;
  timestamp: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  isPhishing: boolean;
  confidence: number; // 0-100
  
  indicators: RiskIndicator[];
  safeDomain?: string;
  recommendation: string;
  
  // Additional analysis
  domainAge?: number;
  sslStatus?: SSLStatus;
  similarDomains?: string[];
  blacklistStatus?: BlacklistStatus;
}

export interface RiskIndicator {
  type: 'domain' | 'url' | 'ssl' | 'content' | 'reputation';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  details?: string;
}

export interface SSLStatus {
  isValid: boolean;
  issuer?: string;
  expiryDate?: string;
  issues: string[];
}

export interface BlacklistStatus {
  isBlacklisted: boolean;
  sources: string[];
  category?: string;
  lastUpdated?: string;
}

// Password Rotation Types
export interface RotationPlanRequest {
  requestId: string;
  userId: string;
  passwords: PasswordEntry[];
  prioritySites?: string[];
  rotationFrequency?: 'weekly' | 'monthly' | 'quarterly' | 'annual';
  userPreferences?: RotationPreferences;
}

export interface RotationPreferences {
  maxPasswordsPerWeek?: number;
  preferredDays?: string[]; // ['monday', 'wednesday']
  avoidBusyPeriods?: boolean;
  reminderPreference?: 'email' | 'push' | 'sms' | 'none';
  autoRotateWhenPossible?: boolean;
}

export interface RotationPlanResult {
  requestId: string;
  userId: string;
  timestamp: string;
  
  totalPasswords: number;
  rotationSchedule: RotationScheduleItem[];
  criticalPriority: string[]; // entry IDs requiring immediate attention
  estimatedTimeRequired: number; // total hours
  
  // Detailed planning
  monthlyBreakdown: MonthlyRotationPlan[];
  instructions: SiteRotationInstruction[];
  summary: string;
  
  // Progress tracking
  completionEstimate: string; // ISO date
  milestones: RotationMilestone[];
}

export interface RotationScheduleItem {
  entryId: string;
  site: string;
  priority: 'IMMEDIATE' | 'HIGH' | 'MEDIUM' | 'LOW';
  scheduledDate: string; // ISO date
  estimatedMinutes: number;
  category: string;
  requirements?: string[]; // special requirements for this site
}

export interface MonthlyRotationPlan {
  month: string; // "2024-01"
  passwordCount: number;
  estimatedHours: number;
  priorities: {
    immediate: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface SiteRotationInstruction {
  site: string;
  category: string;
  steps: string[];
  requirements: string[]; // "MFA required", "Security questions needed"
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: number;
  tips?: string[];
}

export interface RotationMilestone {
  date: string;
  description: string;
  passwordCount: number;
  completionPercentage: number;
}

// API Response wrappers
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    requestId: string;
    timestamp: string;
    processingTime: number;
    rateLimit?: {
      remaining: number;
      resetTime: string;
    };
  };
}

export interface PaginatedResponse<T = any> extends APIResponse<T> {
  pagination?: {
    page: number;
    limit: number;
    total: number;
    hasMore: boolean;
  };
}

// User context and preferences
export interface UserContext {
  userId: string;
  tier: 'free' | 'plus' | 'pro' | 'family' | 'enterprise';
  preferences: UserPreferences;
  limits: UserLimits;
  features: string[];
}

export interface UserPreferences {
  analysisDepth: 'basic' | 'standard' | 'comprehensive';
  reportFormat: 'executive' | 'technical' | 'user-friendly';
  notificationFrequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  includeTrendAnalysis: boolean;
  includeComplianceCheck: boolean;
  autoRunScheduledAudits: boolean;
  language: string;
  timezone: string;
}

export interface UserLimits {
  maxPasswordsPerAudit: number;
  auditsPerMonth: number;
  phishingChecksPerDay: number;
  rotationPlansPerMonth: number;
  maxHistoricalData: number; // days
  advancedFeaturesEnabled: boolean;
}

// Error types
export interface IntelligenceError extends Error {
  code: string;
  statusCode: number;
  details?: any;
}

// Event types for analytics
export interface AnalyticsEvent {
  userId: string;
  eventType: 'audit_completed' | 'phishing_detected' | 'rotation_planned' | 'security_improved';
  timestamp: string;
  data: any;
  metadata?: {
    userAgent?: string;
    ip?: string;
    sessionId?: string;
  };
}

// Webhook types for integrations
export interface WebhookPayload {
  event: string;
  userId: string;
  timestamp: string;
  data: any;
  signature?: string;
}

export interface IntegrationConfig {
  webhookUrl?: string;
  apiKey?: string;
  enabled: boolean;
  events: string[];
  retryPolicy?: {
    maxRetries: number;
    backoffMultiplier: number;
  };
}
