import { Eko, LLMs } from '@eko-ai/eko';
import { BrowserAgent, FileAgent } from '@eko-ai/eko-nodejs';
import type { 
  VaultAuditRequest, 
  VaultAuditResult, 
  PhishingCheckRequest, 
  PhishingCheckResult,
  RotationPlanRequest,
  RotationPlanResult 
} from '../types/intelligence.js';

export class EkoService {
  private eko: Eko;
  private llms: LLMs;

  constructor() {
    // Initialize LLM configurations based on environment
    this.llms = this.initializeLLMs();
    
    // Initialize with basic agents for now
    const agents = [
      new BrowserAgent(),
      new FileAgent()
    ];

    // Create Eko instance
    this.eko = new Eko({ 
      llms: this.llms, 
      agents 
    });
  }

  private initializeLLMs(): LLMs {
    const llms: LLMs = {};

    // Default LLM (required)
    const defaultProvider = process.env.DEFAULT_LLM_PROVIDER || 'anthropic';
    const defaultModel = process.env.DEFAULT_LLM_MODEL || 'claude-3-5-sonnet-20241022';

    switch (defaultProvider) {
      case 'anthropic':
        llms.default = {
          provider: 'anthropic',
          model: defaultModel,
          apiKey: process.env.ANTHROPIC_API_KEY!
        };
        break;
      case 'openai':
        llms.default = {
          provider: 'openai',
          model: defaultModel,
          apiKey: process.env.OPENAI_API_KEY!
        };
        break;
      case 'google':
        llms.default = {
          provider: 'google',
          model: defaultModel,
          apiKey: process.env.GOOGLE_AI_API_KEY!
        };
        break;
    }

    // Add additional LLMs if configured
    if (process.env.ANTHROPIC_API_KEY) {
      llms.claude = {
        provider: 'anthropic',
        model: 'claude-3-5-sonnet-20241022',
        apiKey: process.env.ANTHROPIC_API_KEY
      };
    }

    if (process.env.OPENAI_API_KEY) {
      llms.gpt = {
        provider: 'openai',
        model: 'gpt-4-turbo',
        apiKey: process.env.OPENAI_API_KEY
      };
    }

    if (process.env.GOOGLE_AI_API_KEY) {
      llms.gemini = {
        provider: 'google',
        model: 'gemini-2.5-pro',
        apiKey: process.env.GOOGLE_AI_API_KEY
      };
    }

    return llms;
  }

  /**
   * Perform comprehensive vault security audit
   */
  async auditVault(request: VaultAuditRequest): Promise<VaultAuditResult> {
    const prompt = `
Perform a comprehensive security audit of this password vault:

Vault Data:
${JSON.stringify(request.passwords, null, 2)}

Analysis Required:
1. Identify weak passwords (< 12 chars, no special chars, common patterns)
2. Find duplicate passwords across entries
3. Check for passwords that haven't been updated in > 90 days
4. Assess overall security score (0-100)
5. Provide actionable recommendations prioritized by risk

User Context:
- User ID: ${request.userId}
- Vault contains ${request.passwords.length} entries
- Analysis depth: ${request.analysisDepth || 'standard'}

Return results as structured JSON with:
- securityScore (0-100)
- weakPasswords (array of entry IDs and reasons)
- duplicatePasswords (groups of entries sharing passwords)
- stalePasswords (entries not updated in 90+ days)
- recommendations (prioritized action items)
- summary (human-readable executive summary)
`;

    try {
      const result = await this.eko.run(prompt);
      
      // Parse and validate the AI response
      const auditData = this.parseAuditResponse(result.result);
      
      return {
        requestId: request.requestId,
        userId: request.userId,
        timestamp: new Date().toISOString(),
        ...auditData
      };
    } catch (error) {
      throw new Error(`Vault audit failed: ${error}`);
    }
  }

  /**
   * Check if a domain/URL is potentially malicious or phishing
   */
  async checkPhishing(request: PhishingCheckRequest): Promise<PhishingCheckResult> {
    const prompt = `
Analyze this URL/domain for phishing and security risks:

URL: ${request.url}
Context: User is about to ${request.context || 'access this site'}

Analysis Required:
1. Check for domain lookalikes of popular services
2. Assess URL structure for suspicious patterns
3. Check against known phishing indicators
4. Evaluate SSL certificate status (if provided)
5. Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)

Return structured JSON with:
- riskLevel: string ('LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL')
- isPhishing: boolean
- indicators: array of risk indicators found
- safeDomain: suggested safe alternative if applicable
- recommendation: user-facing recommendation
- confidence: analysis confidence (0-100)
`;

    try {
      const result = await this.eko.run(prompt);
      const phishingData = this.parsePhishingResponse(result.result);
      
      return {
        requestId: request.requestId,
        url: request.url,
        timestamp: new Date().toISOString(),
        ...phishingData
      };
    } catch (error) {
      throw new Error(`Phishing check failed: ${error}`);
    }
  }

  /**
   * Generate intelligent password rotation plan
   */
  async createRotationPlan(request: RotationPlanRequest): Promise<RotationPlanResult> {
    const prompt = `
Create an intelligent password rotation plan for this user's vault:

Vault Overview:
- Total entries: ${request.passwords.length}
- High priority sites: ${request.prioritySites?.join(', ') || 'banking, email, social media'}
- User preference: Rotate ${request.rotationFrequency || 'quarterly'}

Analysis Required:
1. Categorize passwords by security priority (Critical, High, Medium, Low)
2. Assess current password age and strength
3. Create rotation schedule optimized for user burden
4. Generate site-specific guidance for password updates
5. Provide step-by-step action plan

Return structured JSON with:
- totalPasswords: number
- criticalPriority: array of entries needing immediate rotation
- rotationSchedule: monthly plan with entry IDs
- estimatedTimeRequired: hours needed per month
- instructions: site-specific rotation guidance
- summary: executive summary of the plan
`;

    try {
      const result = await this.eko.run(prompt);
      const rotationData = this.parseRotationResponse(result.result);
      
      return {
        requestId: request.requestId,
        userId: request.userId,
        timestamp: new Date().toISOString(),
        ...rotationData
      };
    } catch (error) {
      throw new Error(`Rotation plan creation failed: ${error}`);
    }
  }

  /**
   * Execute custom intelligence task with human-in-the-loop
   */
  async executeCustomTask(task: string, context?: any): Promise<any> {
    try {
      const result = await this.eko.run(task, { context });
      return result;
    } catch (error) {
      throw new Error(`Custom task execution failed: ${error}`);
    }
  }

  private parseAuditResponse(response: string): Partial<VaultAuditResult> {
    try {
      // Try to parse as JSON first
      const parsed = JSON.parse(response);
      return parsed;
    } catch {
      // Fallback: extract key information using regex/parsing
      return {
        securityScore: this.extractSecurityScore(response),
        weakPasswords: this.extractWeakPasswords(response),
        duplicatePasswords: this.extractDuplicatePasswords(response),
        stalePasswords: this.extractStalePasswords(response),
        recommendations: this.extractRecommendations(response),
        summary: this.extractSummary(response)
      };
    }
  }

  private parsePhishingResponse(response: string): Partial<PhishingCheckResult> {
    try {
      return JSON.parse(response);
    } catch {
      return {
        riskLevel: this.extractRiskLevel(response) as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
        isPhishing: response.toLowerCase().includes('phishing') || response.toLowerCase().includes('malicious'),
        indicators: this.extractIndicators(response),
        recommendation: this.extractRecommendation(response),
        confidence: this.extractConfidence(response)
      };
    }
  }

  private parseRotationResponse(response: string): Partial<RotationPlanResult> {
    try {
      return JSON.parse(response);
    } catch {
      return {
        totalPasswords: this.extractTotalPasswords(response),
        criticalPriority: this.extractCriticalPriority(response),
        estimatedTimeRequired: this.extractTimeRequired(response),
        summary: this.extractSummary(response)
      };
    }
  }

  // Helper methods for parsing fallbacks
  private extractSecurityScore(text: string): number {
    const match = text.match(/security.*score.*?(\d+)/i);
    return match ? parseInt(match[1]) : 50; // Default moderate score
  }

  private extractWeakPasswords(text: string): any[] {
    // Implement regex parsing for weak passwords
    return [];
  }

  private extractDuplicatePasswords(text: string): any[] {
    return [];
  }

  private extractStalePasswords(text: string): any[] {
    return [];
  }

  private extractRecommendations(text: string): string[] {
    return [];
  }

  private extractSummary(text: string): string {
    // Extract summary section or use first paragraph
    const summaryMatch = text.match(/summary:?\\s*(.+?)(?:\\n\\n|$)/i);
    return summaryMatch ? summaryMatch[1] : text.substring(0, 200) + '...';
  }

  private extractRiskLevel(text: string): string {
    const riskMatch = text.match(/risk.*level.*?(low|medium|high|critical)/i);
    return riskMatch ? riskMatch[1].toUpperCase() : 'MEDIUM';
  }

  private extractIndicators(text: string): string[] {
    return [];
  }

  private extractRecommendation(text: string): string {
    return text.substring(0, 200) + '...';
  }

  private extractConfidence(text: string): number {
    const match = text.match(/confidence.*?(\d+)/i);
    return match ? parseInt(match[1]) : 75;
  }

  private extractTotalPasswords(text: string): number {
    const match = text.match(/total.*passwords.*?(\d+)/i);
    return match ? parseInt(match[1]) : 0;
  }

  private extractCriticalPriority(text: string): any[] {
    return [];
  }

  private extractTimeRequired(text: string): number {
    const match = text.match(/time.*?(\d+).*hours?/i);
    return match ? parseInt(match[1]) : 2;
  }
}
