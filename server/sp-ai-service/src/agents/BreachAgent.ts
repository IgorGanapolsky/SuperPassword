import { Agent } from '@eko-ai/eko';
import axios from 'axios';
import CryptoJS from 'crypto-js';

export class BreachAgent extends Agent {
  constructor() {
    super();
    this.name = 'BreachAgent';
    this.description = 'Specialized agent for breach detection and monitoring compromised passwords';
  }

  tools = {
    checkHaveIBeenPwned: {
      description: 'Check password against HaveIBeenPwned database',
      parameters: {
        type: 'object',
        properties: {
          passwordHash: { type: 'string', description: 'SHA-1 hash of password' },
          useAPIKey: { type: 'boolean', description: 'Whether to use API key for enhanced features' }
        },
        required: ['passwordHash']
      },
      handler: async ({ passwordHash, useAPIKey = false }: { passwordHash: string; useAPIKey?: boolean }) => {
        try {
          // Use first 5 characters of SHA-1 hash for k-anonymity
          const hashPrefix = passwordHash.substring(0, 5);
          const hashSuffix = passwordHash.substring(5).toUpperCase();
          
          const headers: any = {
            'User-Agent': 'SuperPassword-Security-Check'
          };
          
          if (useAPIKey && process.env.HAVEIBEENPWNED_API_KEY) {
            headers['hibp-api-key'] = process.env.HAVEIBEENPWNED_API_KEY;
          }
          
          const response = await axios.get(
            `https://api.pwnedpasswords.com/range/${hashPrefix}`,
            { 
              headers,
              timeout: 5000 // 5 second timeout
            }
          );
          
          const hashes = response.data.split('\\n');
          const found = hashes.find((line: string) => 
            line.toUpperCase().startsWith(hashSuffix)
          );
          
          if (found) {
            const count = parseInt(found.split(':')[1]);
            return {
              isBreached: true,
              breachCount: count,
              severity: count > 10000 ? 'CRITICAL' : count > 1000 ? 'HIGH' : 'MEDIUM',
              source: 'HaveIBeenPwned',
              recommendation: `This password has been seen ${count.toLocaleString()} times in data breaches. Change it immediately.`
            };
          }
          
          return {
            isBreached: false,
            breachCount: 0,
            severity: 'LOW',
            source: 'HaveIBeenPwned',
            recommendation: 'Password not found in known breaches.'
          };
          
        } catch (error) {
          // Fallback to mock data if API is unavailable
          return this.mockBreachCheck(passwordHash);
        }
      }
    },

    checkBreachMonitoring: {
      description: 'Monitor for new breaches affecting user passwords',
      parameters: {
        type: 'object',
        properties: {
          userHashes: { 
            type: 'array', 
            items: { type: 'string' },
            description: 'Array of password hashes to monitor' 
          },
          lastChecked: { type: 'string', description: 'ISO timestamp of last check' }
        },
        required: ['userHashes']
      },
      handler: async ({ userHashes, lastChecked }: { userHashes: string[]; lastChecked?: string }) => {
        const results = [];
        
        for (const hash of userHashes) {
          const breachResult = await this.tools.checkHaveIBeenPwned.handler({ passwordHash: hash });
          
          if (breachResult.isBreached) {
            results.push({
              hash: hash.substring(0, 8) + '...', // Truncated for privacy
              ...breachResult,
              isNewBreach: this.isNewBreach(lastChecked, breachResult.breachCount)
            });
          }
        }
        
        return {
          totalChecked: userHashes.length,
          breachedCount: results.length,
          newBreaches: results.filter(r => r.isNewBreach).length,
          breachedPasswords: results,
          nextCheckRecommended: this.getNextCheckTime()
        };
      }
    },

    getBreachReport: {
      description: 'Generate comprehensive breach report for user',
      parameters: {
        type: 'object',
        properties: {
          breachData: { 
            type: 'array',
            description: 'Array of breach check results'
          },
          userContext: {
            type: 'object',
            description: 'User context and preferences'
          }
        },
        required: ['breachData']
      },
      handler: async ({ breachData, userContext }: { breachData: any[]; userContext?: any }) => {
        const totalPasswords = breachData.length;
        const breachedPasswords = breachData.filter(item => item.isBreached);
        const criticalBreaches = breachedPasswords.filter(item => item.severity === 'CRITICAL');
        const highRiskBreaches = breachedPasswords.filter(item => item.severity === 'HIGH');
        
        // Calculate risk score
        const riskScore = this.calculateBreachRiskScore(breachedPasswords, totalPasswords);
        
        // Generate prioritized recommendations
        const recommendations = this.generateBreachRecommendations(breachedPasswords);
        
        // Create executive summary
        const summary = this.generateBreachSummary(totalPasswords, breachedPasswords, riskScore);
        
        return {
          timestamp: new Date().toISOString(),
          overview: {
            totalPasswords,
            breachedCount: breachedPasswords.length,
            criticalCount: criticalBreaches.length,
            highRiskCount: highRiskBreaches.length,
            riskScore
          },
          breachedPasswords: breachedPasswords.map(item => ({
            entryId: item.entryId,
            site: item.site,
            severity: item.severity,
            breachCount: item.breachCount,
            recommendation: item.recommendation
          })),
          recommendations,
          summary,
          nextActions: this.getPriorityActions(breachedPasswords)
        };
      }
    },

    checkDomainBreaches: {
      description: 'Check if specific domains have been breached',
      parameters: {
        type: 'object',
        properties: {
          domains: {
            type: 'array',
            items: { type: 'string' },
            description: 'Array of domain names to check'
          }
        },
        required: ['domains']
      },
      handler: async ({ domains }: { domains: string[] }) => {
        const results = [];
        
        for (const domain of domains) {
          try {
            if (process.env.HAVEIBEENPWNED_API_KEY) {
              const headers = {
                'User-Agent': 'SuperPassword-Security-Check',
                'hibp-api-key': process.env.HAVEIBEENPWNED_API_KEY
              };
              
              const response = await axios.get(
                `https://haveibeenpwned.com/api/v3/breaches?domain=${domain}`,
                { headers, timeout: 5000 }
              );
              
              results.push({
                domain,
                hasBreaches: response.data.length > 0,
                breachCount: response.data.length,
                breaches: response.data.map((breach: any) => ({
                  name: breach.Name,
                  breachDate: breach.BreachDate,
                  compromisedAccounts: breach.PwnCount,
                  dataClasses: breach.DataClasses
                }))
              });
            } else {
              // Mock data when API key not available
              results.push(this.mockDomainBreachCheck(domain));
            }
          } catch (error) {
            results.push({
              domain,
              hasBreaches: false,
              breachCount: 0,
              breaches: [],
              error: 'Unable to check domain breaches'
            });
          }
        }
        
        return {
          domainsChecked: domains.length,
          domainsWithBreaches: results.filter(r => r.hasBreaches).length,
          results
        };
      }
    }
  };

  private mockBreachCheck(passwordHash: string): any {
    // Mock implementation for development/testing
    const mockBreachedHashes = ['5e884', 'f25a2', 'd033e', '356a1', '8cb22'];
    const isBreached = mockBreachedHashes.some(hash => passwordHash.startsWith(hash));
    
    if (isBreached) {
      const count = Math.floor(Math.random() * 50000) + 1000;
      return {
        isBreached: true,
        breachCount: count,
        severity: count > 10000 ? 'CRITICAL' : count > 1000 ? 'HIGH' : 'MEDIUM',
        source: 'Mock Data',
        recommendation: `This password has been seen ${count.toLocaleString()} times in data breaches (mock data).`
      };
    }
    
    return {
      isBreached: false,
      breachCount: 0,
      severity: 'LOW',
      source: 'Mock Data',
      recommendation: 'Password not found in known breaches (mock data).'
    };
  }

  private mockDomainBreachCheck(domain: string): any {
    // Mock domain breach data for testing
    const knownBreachedDomains = ['adobe.com', 'linkedin.com', 'yahoo.com', 'equifax.com'];
    const hasBreaches = knownBreachedDomains.includes(domain.toLowerCase());
    
    if (hasBreaches) {
      return {
        domain,
        hasBreaches: true,
        breachCount: Math.floor(Math.random() * 3) + 1,
        breaches: [{
          name: `${domain} Breach`,
          breachDate: '2023-01-01',
          compromisedAccounts: Math.floor(Math.random() * 1000000) + 100000,
          dataClasses: ['Email addresses', 'Passwords', 'Usernames']
        }]
      };
    }
    
    return {
      domain,
      hasBreaches: false,
      breachCount: 0,
      breaches: []
    };
  }

  private isNewBreach(lastChecked?: string, breachCount?: number): boolean {
    if (!lastChecked || !breachCount) return false;
    
    // Simplified logic - in real implementation, would track breach count changes
    const daysSinceCheck = Math.floor(
      (Date.now() - new Date(lastChecked).getTime()) / (1000 * 60 * 60 * 24)
    );
    
    // Consider it a "new" breach if we haven't checked in over 30 days and it's breached
    return daysSinceCheck > 30 && breachCount > 0;
  }

  private getNextCheckTime(): string {
    // Recommend checking again in 7 days
    const nextCheck = new Date();
    nextCheck.setDate(nextCheck.getDate() + 7);
    return nextCheck.toISOString();
  }

  private calculateBreachRiskScore(breachedPasswords: any[], totalPasswords: number): number {
    if (totalPasswords === 0) return 0;
    
    const breachPercentage = (breachedPasswords.length / totalPasswords) * 100;
    const criticalCount = breachedPasswords.filter(p => p.severity === 'CRITICAL').length;
    const highCount = breachedPasswords.filter(p => p.severity === 'HIGH').length;
    
    // Base score from percentage of breached passwords
    let score = breachPercentage;
    
    // Weight critical and high severity breaches more heavily
    score += (criticalCount * 20);
    score += (highCount * 10);
    
    return Math.min(100, Math.round(score));
  }

  private generateBreachRecommendations(breachedPasswords: any[]): string[] {
    const recommendations = [];
    
    const criticalCount = breachedPasswords.filter(p => p.severity === 'CRITICAL').length;
    const highCount = breachedPasswords.filter(p => p.severity === 'HIGH').length;
    
    if (criticalCount > 0) {
      recommendations.push(`🚨 URGENT: Change ${criticalCount} critically compromised password(s) immediately`);
    }
    
    if (highCount > 0) {
      recommendations.push(`⚠️  HIGH PRIORITY: Update ${highCount} high-risk password(s) within 24 hours`);
    }
    
    if (breachedPasswords.length > 5) {
      recommendations.push('📋 Consider using a password manager to generate unique passwords');
    }
    
    if (breachedPasswords.some(p => p.breachCount > 100000)) {
      recommendations.push('🔐 Enable 2FA on all critical accounts immediately');
    }
    
    recommendations.push('🔄 Set up regular password health checks (monthly recommended)');
    
    return recommendations;
  }

  private generateBreachSummary(total: number, breached: any[], riskScore: number): string {
    const percentage = Math.round((breached.length / total) * 100);
    
    if (breached.length === 0) {
      return `Great news! All ${total} of your passwords appear secure with no known breaches detected.`;
    }
    
    const riskLevel = riskScore >= 80 ? 'CRITICAL' : riskScore >= 60 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW';
    
    return `Security Alert: ${breached.length} of your ${total} passwords (${percentage}%) have been found in data breaches. Your overall risk level is ${riskLevel} (score: ${riskScore}/100). Immediate action is recommended to secure your accounts.`;
  }

  private getPriorityActions(breachedPasswords: any[]): string[] {
    const actions = [];
    
    const criticalSites = breachedPasswords
      .filter(p => p.severity === 'CRITICAL')
      .slice(0, 3); // Top 3 most critical
      
    criticalSites.forEach(site => {
      actions.push(`Change password for ${site.site} (seen ${site.breachCount?.toLocaleString()} times in breaches)`);
    });
    
    if (criticalSites.length < breachedPasswords.length) {
      actions.push('Review and update remaining compromised passwords');
    }
    
    actions.push('Enable two-factor authentication where available');
    actions.push('Schedule regular security reviews (monthly)');
    
    return actions;
  }
}
