import { Agent } from '@eko-ai/eko';

export class ReportAgent extends Agent {
  constructor() {
    super();
    this.name = 'ReportAgent';
    this.description = 'Specialized agent for generating comprehensive security reports and summaries';
  }

  tools = {
    generateExecutiveSummary: {
      description: 'Generate executive summary from security analysis data',
      parameters: {
        type: 'object',
        properties: {
          analysisData: {
            type: 'object',
            description: 'Complete security analysis data including scores, risks, and recommendations'
          },
          userContext: {
            type: 'object',
            description: 'User context such as preferences, tier, and history'
          }
        },
        required: ['analysisData']
      },
      handler: async ({ analysisData, userContext }: { analysisData: any; userContext?: any }) => {
        const summary = this.createExecutiveSummary(analysisData, userContext);
        return {
          summary,
          keyMetrics: this.extractKeyMetrics(analysisData),
          riskLevel: this.assessOverallRisk(analysisData),
          priorityActions: this.getPriorityActions(analysisData),
          nextReviewDate: this.calculateNextReview(analysisData)
        };
      }
    },

    formatSecurityReport: {
      description: 'Format comprehensive security report for different audiences',
      parameters: {
        type: 'object',
        properties: {
          reportData: {
            type: 'object',
            description: 'Raw security report data'
          },
          format: {
            type: 'string',
            enum: ['executive', 'technical', 'user-friendly'],
            description: 'Target audience format'
          },
          includeCharts: {
            type: 'boolean',
            description: 'Whether to include chart data'
          }
        },
        required: ['reportData', 'format']
      },
      handler: async ({ reportData, format, includeCharts = false }: { 
        reportData: any; 
        format: 'executive' | 'technical' | 'user-friendly'; 
        includeCharts?: boolean;
      }) => {
        switch (format) {
          case 'executive':
            return this.formatExecutiveReport(reportData, includeCharts);
          case 'technical':
            return this.formatTechnicalReport(reportData, includeCharts);
          case 'user-friendly':
            return this.formatUserFriendlyReport(reportData, includeCharts);
          default:
            throw new Error(`Unsupported format: ${format}`);
        }
      }
    },

    generateRecommendations: {
      description: 'Generate prioritized, actionable security recommendations',
      parameters: {
        type: 'object',
        properties: {
          riskFactors: {
            type: 'array',
            description: 'Array of identified risk factors'
          },
          userProfile: {
            type: 'object',
            description: 'User profile including technical level and preferences'
          },
          timeConstraints: {
            type: 'object',
            description: 'User time availability and urgency preferences'
          }
        },
        required: ['riskFactors']
      },
      handler: async ({ riskFactors, userProfile, timeConstraints }: { 
        riskFactors: any[]; 
        userProfile?: any; 
        timeConstraints?: any;
      }) => {
        const recommendations = this.prioritizeRecommendations(riskFactors, userProfile, timeConstraints);
        return {
          immediate: recommendations.filter(r => r.urgency === 'immediate'),
          thisWeek: recommendations.filter(r => r.urgency === 'week'),
          thisMonth: recommendations.filter(r => r.urgency === 'month'),
          ongoing: recommendations.filter(r => r.urgency === 'ongoing'),
          estimatedTimeRequired: this.calculateTimeRequired(recommendations)
        };
      }
    },

    createSecurityDigest: {
      description: 'Create periodic security digest with trends and updates',
      parameters: {
        type: 'object',
        properties: {
          currentAnalysis: {
            type: 'object',
            description: 'Current security analysis'
          },
          historicalData: {
            type: 'array',
            description: 'Array of historical analysis data'
          },
          timePeriod: {
            type: 'string',
            enum: ['weekly', 'monthly', 'quarterly'],
            description: 'Digest time period'
          }
        },
        required: ['currentAnalysis', 'timePeriod']
      },
      handler: async ({ currentAnalysis, historicalData = [], timePeriod }: { 
        currentAnalysis: any; 
        historicalData?: any[]; 
        timePeriod: 'weekly' | 'monthly' | 'quarterly';
      }) => {
        return {
          period: timePeriod,
          timestamp: new Date().toISOString(),
          summary: this.createDigestSummary(currentAnalysis, historicalData, timePeriod),
          trends: this.analyzeTrends(currentAnalysis, historicalData),
          achievements: this.identifyAchievements(currentAnalysis, historicalData),
          alerts: this.generateAlerts(currentAnalysis),
          nextSteps: this.suggestNextSteps(currentAnalysis, timePeriod)
        };
      }
    }
  };

  private createExecutiveSummary(analysisData: any, userContext?: any): string {
    const { securityScore = 0, totalPasswords = 0, weakPasswords = [], breachedPasswords = [] } = analysisData;
    
    const riskLevel = securityScore >= 80 ? 'LOW' : securityScore >= 60 ? 'MODERATE' : securityScore >= 40 ? 'HIGH' : 'CRITICAL';
    const weakCount = weakPasswords.length || 0;
    const breachedCount = breachedPasswords.length || 0;
    
    if (riskLevel === 'LOW') {
      return `Excellent security posture! Your ${totalPasswords} passwords maintain a strong security score of ${securityScore}/100 with minimal vulnerabilities detected. Continue current practices and monitor for emerging threats.`;
    } else if (riskLevel === 'MODERATE') {
      return `Good security foundation with room for improvement. Your ${totalPasswords} passwords scored ${securityScore}/100. Focus on addressing ${weakCount} weak passwords and ${breachedCount} compromised credentials to enhance your security posture.`;
    } else if (riskLevel === 'HIGH') {
      return `Security vulnerabilities require immediate attention. Of your ${totalPasswords} passwords, ${weakCount} are weak and ${breachedCount} have been compromised in data breaches. Your current score of ${securityScore}/100 indicates significant risk that should be addressed promptly.`;
    } else {
      return `CRITICAL security issues detected! Your password vault requires immediate action with a security score of ${securityScore}/100. ${breachedCount} passwords are compromised and ${weakCount} are critically weak. Immediate remediation is essential to protect your accounts.`;
    }
  }

  private extractKeyMetrics(analysisData: any): any {
    return {
      totalPasswords: analysisData.totalPasswords || 0,
      securityScore: analysisData.securityScore || 0,
      weakPasswords: (analysisData.weakPasswords || []).length,
      breachedPasswords: (analysisData.breachedPasswords || []).length,
      duplicatePasswords: (analysisData.duplicatePasswords || []).length,
      stalePasswords: (analysisData.stalePasswords || []).length,
      averagePasswordAge: this.calculateAverageAge(analysisData.passwords || []),
      strongPasswordsPercentage: this.calculateStrongPasswordsPercentage(analysisData)
    };
  }

  private assessOverallRisk(analysisData: any): string {
    const score = analysisData.securityScore || 0;
    const breachedCount = (analysisData.breachedPasswords || []).length;
    const weakCount = (analysisData.weakPasswords || []).length;
    const total = analysisData.totalPasswords || 1;
    
    // Factor in breach and weakness percentages
    const breachedPercentage = (breachedCount / total) * 100;
    const weakPercentage = (weakCount / total) * 100;
    
    if (score >= 80 && breachedPercentage < 5 && weakPercentage < 10) {
      return 'LOW';
    } else if (score >= 60 && breachedPercentage < 15 && weakPercentage < 25) {
      return 'MODERATE';
    } else if (score >= 40 || breachedPercentage < 30) {
      return 'HIGH';
    } else {
      return 'CRITICAL';
    }
  }

  private getPriorityActions(analysisData: any): string[] {
    const actions = [];
    const breachedCount = (analysisData.breachedPasswords || []).length;
    const weakCount = (analysisData.weakPasswords || []).length;
    const duplicateCount = (analysisData.duplicatePasswords || []).length;
    const staleCount = (analysisData.stalePasswords || []).length;
    
    if (breachedCount > 0) {
      actions.push(`🚨 Change ${breachedCount} compromised password${breachedCount > 1 ? 's' : ''} immediately`);
    }
    
    if (weakCount > 3) {
      actions.push(`🔐 Strengthen ${weakCount} weak password${weakCount > 1 ? 's' : ''}`);
    }
    
    if (duplicateCount > 0) {
      actions.push(`🔄 Replace ${duplicateCount} duplicate password${duplicateCount > 1 ? 's' : ''} with unique ones`);
    }
    
    if (staleCount > 5) {
      actions.push(`⏰ Update ${staleCount} password${staleCount > 1 ? 's' : ''} that haven't been changed in 90+ days`);
    }
    
    if (actions.length === 0) {
      actions.push('✅ Maintain current security practices and monitor regularly');
    }
    
    return actions.slice(0, 5); // Top 5 priority actions
  }

  private calculateNextReview(analysisData: any): string {
    const riskLevel = this.assessOverallRisk(analysisData);
    const nextReview = new Date();
    
    switch (riskLevel) {
      case 'CRITICAL':
        nextReview.setDate(nextReview.getDate() + 7); // 1 week
        break;
      case 'HIGH':
        nextReview.setDate(nextReview.getDate() + 14); // 2 weeks
        break;
      case 'MODERATE':
        nextReview.setDate(nextReview.getDate() + 30); // 1 month
        break;
      case 'LOW':
        nextReview.setDate(nextReview.getDate() + 90); // 3 months
        break;
    }
    
    return nextReview.toISOString();
  }

  private formatExecutiveReport(reportData: any, includeCharts: boolean): any {
    return {
      title: 'Executive Security Summary',
      executiveSummary: this.createExecutiveSummary(reportData),
      keyMetrics: this.extractKeyMetrics(reportData),
      riskAssessment: {
        overallRisk: this.assessOverallRisk(reportData),
        criticalFindings: this.getCriticalFindings(reportData),
        recommendations: this.getPriorityActions(reportData).slice(0, 3)
      },
      ...(includeCharts && { chartData: this.generateChartData(reportData) })
    };
  }

  private formatTechnicalReport(reportData: any, includeCharts: boolean): any {
    return {
      title: 'Technical Security Analysis',
      analysisDetails: reportData,
      securityMetrics: this.extractKeyMetrics(reportData),
      vulnerabilities: {
        weak: reportData.weakPasswords || [],
        breached: reportData.breachedPasswords || [],
        duplicate: reportData.duplicatePasswords || [],
        stale: reportData.stalePasswords || []
      },
      recommendations: reportData.recommendations || [],
      ...(includeCharts && { chartData: this.generateChartData(reportData) })
    };
  }

  private formatUserFriendlyReport(reportData: any, includeCharts: boolean): any {
    const score = reportData.securityScore || 0;
    const emoji = score >= 80 ? '🎉' : score >= 60 ? '👍' : score >= 40 ? '⚠️' : '🚨';
    
    return {
      title: `${emoji} Your Password Security Report`,
      yourScore: {
        score,
        grade: this.getLetterGrade(score),
        message: this.getUserFriendlyMessage(score)
      },
      quickWins: this.getQuickWins(reportData),
      nextSteps: this.getPriorityActions(reportData).slice(0, 3),
      ...(includeCharts && { chartData: this.generateChartData(reportData) })
    };
  }

  private prioritizeRecommendations(riskFactors: any[], userProfile?: any, timeConstraints?: any): any[] {
    const recommendations = [];
    
    for (const risk of riskFactors) {
      const recommendation = this.createRecommendation(risk, userProfile, timeConstraints);
      recommendations.push(recommendation);
    }
    
    // Sort by urgency and impact
    return recommendations.sort((a, b) => {
      const urgencyOrder = { immediate: 0, week: 1, month: 2, ongoing: 3 };
      return urgencyOrder[a.urgency] - urgencyOrder[b.urgency] || b.impact - a.impact;
    });
  }

  private createRecommendation(risk: any, userProfile?: any, timeConstraints?: any): any {
    const isAdvancedUser = userProfile?.technicalLevel === 'advanced';
    const hasLimitedTime = timeConstraints?.timeAvailable === 'limited';
    
    return {
      id: `rec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title: risk.title || 'Security Recommendation',
      description: isAdvancedUser ? risk.technicalDescription : risk.userDescription,
      urgency: this.calculateUrgency(risk),
      impact: risk.impact || 50,
      estimatedMinutes: hasLimitedTime ? Math.min(risk.estimatedMinutes, 15) : risk.estimatedMinutes,
      steps: risk.steps || [],
      category: risk.category || 'general'
    };
  }

  private calculateUrgency(risk: any): 'immediate' | 'week' | 'month' | 'ongoing' {
    if (risk.severity === 'CRITICAL' || risk.type === 'breach') return 'immediate';
    if (risk.severity === 'HIGH' || risk.type === 'weak') return 'week';
    if (risk.severity === 'MEDIUM' || risk.type === 'duplicate') return 'month';
    return 'ongoing';
  }

  // Helper methods
  private calculateAverageAge(passwords: any[]): number {
    if (!passwords.length) return 0;
    const totalDays = passwords.reduce((sum, pwd) => {
      const lastUpdated = pwd.lastUpdated ? new Date(pwd.lastUpdated) : new Date(0);
      const daysSince = Math.floor((Date.now() - lastUpdated.getTime()) / (1000 * 60 * 60 * 24));
      return sum + daysSince;
    }, 0);
    return Math.round(totalDays / passwords.length);
  }

  private calculateStrongPasswordsPercentage(analysisData: any): number {
    const total = analysisData.totalPasswords || 0;
    if (total === 0) return 0;
    
    const weak = (analysisData.weakPasswords || []).length;
    const strong = total - weak;
    return Math.round((strong / total) * 100);
  }

  private getCriticalFindings(reportData: any): string[] {
    const findings = [];
    const breachedCount = (reportData.breachedPasswords || []).length;
    const weakCount = (reportData.weakPasswords || []).length;
    const duplicateCount = (reportData.duplicatePasswords || []).length;
    
    if (breachedCount > 0) {
      findings.push(`${breachedCount} passwords found in data breaches`);
    }
    if (weakCount > 5) {
      findings.push(`${weakCount} passwords below minimum strength requirements`);
    }
    if (duplicateCount > 3) {
      findings.push(`${duplicateCount} duplicate passwords increase attack surface`);
    }
    
    return findings;
  }

  private getLetterGrade(score: number): string {
    if (score >= 90) return 'A+';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B';
    if (score >= 60) return 'C';
    if (score >= 50) return 'D';
    return 'F';
  }

  private getUserFriendlyMessage(score: number): string {
    if (score >= 80) return 'Great job! Your passwords are well-protected.';
    if (score >= 60) return 'Good progress! A few improvements will boost your security.';
    if (score >= 40) return 'Your passwords need attention to stay secure.';
    return 'Let\'s work together to secure your accounts properly.';
  }

  private getQuickWins(reportData: any): string[] {
    const wins = [];
    const weak = (reportData.weakPasswords || []).slice(0, 3);
    const breached = (reportData.breachedPasswords || []).slice(0, 2);
    
    breached.forEach(pwd => {
      wins.push(`Update your ${pwd.site} password (found in breach)`);
    });
    
    weak.forEach(pwd => {
      wins.push(`Strengthen your ${pwd.site} password`);
    });
    
    return wins;
  }

  private generateChartData(reportData: any): any {
    const total = reportData.totalPasswords || 0;
    const weak = (reportData.weakPasswords || []).length;
    const breached = (reportData.breachedPasswords || []).length;
    const duplicate = (reportData.duplicatePasswords || []).length;
    const strong = total - weak - breached - duplicate;
    
    return {
      passwordStrength: {
        strong,
        weak,
        breached,
        duplicate
      },
      securityTrend: [
        { date: '30 days ago', score: Math.max(0, (reportData.securityScore || 0) - 15) },
        { date: '7 days ago', score: Math.max(0, (reportData.securityScore || 0) - 5) },
        { date: 'Today', score: reportData.securityScore || 0 }
      ]
    };
  }

  private calculateTimeRequired(recommendations: any[]): any {
    const immediate = recommendations.filter(r => r.urgency === 'immediate').reduce((sum, r) => sum + r.estimatedMinutes, 0);
    const week = recommendations.filter(r => r.urgency === 'week').reduce((sum, r) => sum + r.estimatedMinutes, 0);
    const month = recommendations.filter(r => r.urgency === 'month').reduce((sum, r) => sum + r.estimatedMinutes, 0);
    
    return {
      immediate: `${immediate} minutes`,
      thisWeek: `${Math.round(week / 60)} hours`,
      thisMonth: `${Math.round(month / 60)} hours`
    };
  }

  private createDigestSummary(current: any, historical: any[], period: string): string {
    const improvement = historical.length > 0 ? 
      (current.securityScore || 0) - (historical[historical.length - 1]?.securityScore || 0) : 0;
    
    const trend = improvement > 5 ? 'improved significantly' : 
                 improvement > 0 ? 'improved slightly' : 
                 improvement === 0 ? 'remained stable' : 'needs attention';
    
    return `Your password security has ${trend} over the past ${period}. Current score: ${current.securityScore || 0}/100.`;
  }

  private analyzeTrends(current: any, historical: any[]): any {
    if (historical.length < 2) return { trend: 'insufficient_data' };
    
    const scores = historical.map(h => h.securityScore || 0);
    const avgImprovement = scores.reduce((sum, score, i) => {
      if (i === 0) return sum;
      return sum + (score - scores[i - 1]);
    }, 0) / (scores.length - 1);
    
    return {
      trend: avgImprovement > 2 ? 'improving' : avgImprovement < -2 ? 'declining' : 'stable',
      averageImprovement: Math.round(avgImprovement * 10) / 10,
      consistentImprovement: scores.every((score, i) => i === 0 || score >= scores[i - 1])
    };
  }

  private identifyAchievements(current: any, historical: any[]): string[] {
    const achievements = [];
    
    if (current.securityScore >= 80) {
      achievements.push('🏆 Achieved excellent security score (80+)');
    }
    
    if ((current.breachedPasswords || []).length === 0) {
      achievements.push('🛡️ Zero compromised passwords');
    }
    
    if (historical.length > 0) {
      const lastScore = historical[historical.length - 1]?.securityScore || 0;
      if ((current.securityScore || 0) > lastScore + 10) {
        achievements.push('📈 Improved security score by 10+ points');
      }
    }
    
    return achievements;
  }

  private generateAlerts(current: any): string[] {
    const alerts = [];
    const breached = (current.breachedPasswords || []).length;
    const weak = (current.weakPasswords || []).length;
    
    if (breached > 0) {
      alerts.push(`🚨 ${breached} password${breached > 1 ? 's' : ''} compromised in breaches`);
    }
    
    if (weak > current.totalPasswords * 0.3) {
      alerts.push(`⚠️ ${Math.round((weak / current.totalPasswords) * 100)}% of passwords are weak`);
    }
    
    return alerts;
  }

  private suggestNextSteps(current: any, period: string): string[] {
    const steps = [];
    const riskLevel = this.assessOverallRisk(current);
    
    if (riskLevel === 'CRITICAL' || riskLevel === 'HIGH') {
      steps.push('Focus on fixing critical security issues first');
      steps.push('Schedule daily password updates until resolved');
    } else if (riskLevel === 'MODERATE') {
      steps.push('Gradually improve weak passwords');
      steps.push('Enable 2FA on important accounts');
    } else {
      steps.push('Maintain current security practices');
      steps.push('Monitor for new threats and breaches');
    }
    
    if (period === 'weekly') {
      steps.push('Review and update 2-3 passwords');
    } else if (period === 'monthly') {
      steps.push('Perform comprehensive security review');
    }
    
    return steps;
  }
}
