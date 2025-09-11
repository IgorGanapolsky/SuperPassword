import { Agent } from '@eko-ai/eko';
import CryptoJS from 'crypto-js';

export class SecurityAgent extends Agent {
  constructor() {
    super();
    this.name = 'SecurityAgent';
    this.description = 'Specialized agent for password security analysis and vulnerability detection';
  }

  tools = {
    analyzePassword: {
      description: 'Analyze password strength and security metrics',
      parameters: {
        type: 'object',
        properties: {
          password: { type: 'string', description: 'Password to analyze (will be hashed)' },
          context: { type: 'string', description: 'Context about where password is used' }
        },
        required: ['password']
      },
      handler: async ({ password, context }: { password: string; context?: string }) => {
        // Hash the password for security - never store plaintext
        const passwordHash = CryptoJS.SHA256(password).toString();
        
        const analysis = {
          length: password.length,
          hasUppercase: /[A-Z]/.test(password),
          hasLowercase: /[a-z]/.test(password),
          hasNumbers: /\d/.test(password),
          hasSpecialChars: /[!@#$%^&*(),.?":{}|<>]/.test(password),
          isCommon: this.checkCommonPassword(password),
          patterns: this.detectPatterns(password),
          entropy: this.calculateEntropy(password),
          hash: passwordHash.substring(0, 8) // Only store first 8 chars of hash for comparison
        };

        const score = this.calculateSecurityScore(analysis);
        
        return {
          score,
          strength: score >= 80 ? 'Strong' : score >= 60 ? 'Moderate' : score >= 40 ? 'Weak' : 'Very Weak',
          analysis,
          recommendations: this.generateRecommendations(analysis),
          context
        };
      }
    },

    checkBreachStatus: {
      description: 'Check if password hash appears in known breach databases',
      parameters: {
        type: 'object',
        properties: {
          passwordHash: { type: 'string', description: 'SHA256 hash of password' }
        },
        required: ['passwordHash']
      },
      handler: async ({ passwordHash }: { passwordHash: string }) => {
        // In a real implementation, this would check against HaveIBeenPwned API
        // For now, return mock data based on hash patterns
        const isBreached = this.mockBreachCheck(passwordHash);
        
        return {
          isBreached,
          breachCount: isBreached ? Math.floor(Math.random() * 10000) + 1 : 0,
          severity: isBreached ? 'HIGH' : 'LOW',
          recommendation: isBreached ? 
            'This password has been found in data breaches. Change it immediately.' :
            'No known breaches detected for this password.'
        };
      }
    },

    categorizeRisk: {
      description: 'Categorize password entry by security risk level',
      parameters: {
        type: 'object',
        properties: {
          entry: { 
            type: 'object',
            description: 'Password entry with site, username, password, lastUpdated',
            properties: {
              site: { type: 'string' },
              username: { type: 'string' },
              password: { type: 'string' },
              lastUpdated: { type: 'string' }
            }
          }
        },
        required: ['entry']
      },
      handler: async ({ entry }: { entry: any }) => {
        const passwordAnalysis = await this.tools.analyzePassword.handler({ 
          password: entry.password, 
          context: entry.site 
        });
        
        const breachCheck = await this.tools.checkBreachStatus.handler({
          passwordHash: CryptoJS.SHA256(entry.password).toString()
        });

        const daysSinceUpdate = entry.lastUpdated ? 
          Math.floor((Date.now() - new Date(entry.lastUpdated).getTime()) / (1000 * 60 * 60 * 24)) : 
          999;

        // Risk factors
        const riskFactors = {
          weakPassword: passwordAnalysis.score < 60,
          breached: breachCheck.isBreached,
          stale: daysSinceUpdate > 90,
          criticalSite: this.isCriticalSite(entry.site),
          duplicatePassword: false // Will be set by duplicate detection
        };

        const riskScore = this.calculateRiskScore(riskFactors, passwordAnalysis.score);
        
        return {
          entryId: entry.id || `${entry.site}_${entry.username}`,
          site: entry.site,
          riskLevel: riskScore >= 80 ? 'CRITICAL' : riskScore >= 60 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW',
          riskScore,
          riskFactors,
          passwordScore: passwordAnalysis.score,
          daysSinceUpdate,
          recommendations: [
            ...passwordAnalysis.recommendations,
            ...(breachCheck.isBreached ? ['Change password immediately - found in breach'] : []),
            ...(daysSinceUpdate > 180 ? ['Consider updating - password is very old'] : 
               daysSinceUpdate > 90 ? ['Consider updating - password is getting old'] : [])
          ]
        };
      }
    }
  };

  private calculateSecurityScore(analysis: any): number {
    let score = 0;
    
    // Length scoring (0-30 points)
    if (analysis.length >= 16) score += 30;
    else if (analysis.length >= 12) score += 25;
    else if (analysis.length >= 8) score += 15;
    else score += 5;

    // Character variety (0-40 points)
    if (analysis.hasUppercase) score += 10;
    if (analysis.hasLowercase) score += 10;
    if (analysis.hasNumbers) score += 10;
    if (analysis.hasSpecialChars) score += 10;

    // Entropy bonus (0-20 points)
    if (analysis.entropy >= 60) score += 20;
    else if (analysis.entropy >= 50) score += 15;
    else if (analysis.entropy >= 40) score += 10;
    else if (analysis.entropy >= 30) score += 5;

    // Pattern penalties
    if (analysis.patterns.sequential) score -= 10;
    if (analysis.patterns.repeated) score -= 10;
    if (analysis.patterns.keyboard) score -= 5;

    // Common password penalty (0-10 points)
    if (analysis.isCommon) score -= 20;

    return Math.max(0, Math.min(100, score));
  }

  private calculateEntropy(password: string): number {
    const charSets = [];
    if (/[a-z]/.test(password)) charSets.push(26);
    if (/[A-Z]/.test(password)) charSets.push(26);
    if (/\d/.test(password)) charSets.push(10);
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) charSets.push(32);
    
    const charsetSize = charSets.reduce((sum, size) => sum + size, 0);
    return password.length * Math.log2(charsetSize);
  }

  private detectPatterns(password: string): any {
    return {
      sequential: this.hasSequentialChars(password),
      repeated: this.hasRepeatedChars(password),
      keyboard: this.hasKeyboardPattern(password),
      datePattern: this.hasDatePattern(password)
    };
  }

  private hasSequentialChars(password: string): boolean {
    for (let i = 0; i < password.length - 2; i++) {
      const char1 = password.charCodeAt(i);
      const char2 = password.charCodeAt(i + 1);
      const char3 = password.charCodeAt(i + 2);
      if (char2 === char1 + 1 && char3 === char2 + 1) return true;
    }
    return false;
  }

  private hasRepeatedChars(password: string): boolean {
    return /(.)\1{2,}/.test(password);
  }

  private hasKeyboardPattern(password: string): boolean {
    const keyboardRows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm', '1234567890'];
    return keyboardRows.some(row => 
      password.toLowerCase().includes(row.substring(0, 3)) ||
      password.toLowerCase().includes(row.substring(0, 4))
    );
  }

  private hasDatePattern(password: string): boolean {
    return /\d{4}|\d{2}\/\d{2}|\d{2}-\d{2}/.test(password);
  }

  private checkCommonPassword(password: string): boolean {
    const commonPasswords = [
      'password', '123456', '123456789', 'qwerty', 'abc123',
      'password123', 'admin', 'letmein', 'welcome', 'monkey',
      'dragon', 'master', 'sunshine', 'princess', 'football'
    ];
    return commonPasswords.includes(password.toLowerCase());
  }

  private mockBreachCheck(passwordHash: string): boolean {
    // Mock implementation - in real app, use HaveIBeenPwned API
    // Return true for certain hash patterns to simulate breached passwords
    const breachedPatterns = ['a', 'b', 'c', '1', '2'];
    return breachedPatterns.some(pattern => passwordHash.startsWith(pattern));
  }

  private isCriticalSite(site: string): boolean {
    const criticalSites = [
      'bank', 'paypal', 'credit', 'investment', 'trading',
      'amazon', 'apple', 'google', 'microsoft', 'facebook',
      'email', 'gmail', 'outlook', 'icloud', 'work'
    ];
    return criticalSites.some(critical => site.toLowerCase().includes(critical));
  }

  private calculateRiskScore(factors: any, passwordScore: number): number {
    let risk = 0;
    
    // Base risk from password weakness
    risk += Math.max(0, 100 - passwordScore);
    
    // Additional risk factors
    if (factors.breached) risk += 40;
    if (factors.stale) risk += 20;
    if (factors.criticalSite) risk += 15;
    if (factors.duplicatePassword) risk += 25;
    
    return Math.min(100, risk);
  }

  private generateRecommendations(analysis: any): string[] {
    const recommendations = [];
    
    if (analysis.length < 12) {
      recommendations.push('Increase length to at least 12 characters');
    }
    
    if (!analysis.hasUppercase) {
      recommendations.push('Add uppercase letters');
    }
    
    if (!analysis.hasLowercase) {
      recommendations.push('Add lowercase letters');
    }
    
    if (!analysis.hasNumbers) {
      recommendations.push('Add numbers');
    }
    
    if (!analysis.hasSpecialChars) {
      recommendations.push('Add special characters');
    }
    
    if (analysis.isCommon) {
      recommendations.push('Avoid common passwords - create something unique');
    }
    
    if (analysis.patterns.sequential) {
      recommendations.push('Avoid sequential characters (abc, 123)');
    }
    
    if (analysis.patterns.repeated) {
      recommendations.push('Avoid repeated characters (aaa, 111)');
    }
    
    if (analysis.patterns.keyboard) {
      recommendations.push('Avoid keyboard patterns (qwerty, asdf)');
    }
    
    return recommendations;
  }
}
