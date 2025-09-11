import { FastifyInstance, FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { 
  VaultAuditRequest, 
  VaultAuditResult,
  PhishingCheckRequest,
  PhishingCheckResult,
  RotationPlanRequest,
  RotationPlanResult,
  APIResponse
} from '../types/intelligence.js';

// Zod schemas for validation
const PasswordEntrySchema = z.object({
  id: z.string().optional(),
  site: z.string().min(1),
  username: z.string().min(1),
  password: z.string().min(1),
  lastUpdated: z.string().optional(),
  category: z.string().optional(),
  notes: z.string().optional()
});

const VaultAuditRequestSchema = z.object({
  requestId: z.string().uuid(),
  passwords: z.array(PasswordEntrySchema).min(1).max(1000),
  analysisDepth: z.enum(['basic', 'standard', 'comprehensive']).optional().default('standard'),
  includeBreachCheck: z.boolean().optional().default(true),
  includeTrendAnalysis: z.boolean().optional().default(false)
});

const PhishingCheckRequestSchema = z.object({
  requestId: z.string().uuid(),
  url: z.string().url(),
  context: z.string().optional(),
  userAgent: z.string().optional(),
  referrer: z.string().optional()
});

const RotationPlanRequestSchema = z.object({
  requestId: z.string().uuid(),
  passwords: z.array(PasswordEntrySchema).min(1).max(1000),
  prioritySites: z.array(z.string()).optional(),
  rotationFrequency: z.enum(['weekly', 'monthly', 'quarterly', 'annual']).optional().default('monthly'),
  userPreferences: z.object({
    maxPasswordsPerWeek: z.number().optional(),
    preferredDays: z.array(z.string()).optional(),
    avoidBusyPeriods: z.boolean().optional(),
    reminderPreference: z.enum(['email', 'push', 'sms', 'none']).optional(),
    autoRotateWhenPossible: z.boolean().optional()
  }).optional()
});

const intelligenceRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  
  // Vault Security Audit
  fastify.post<{ Body: VaultAuditRequest }>('/audit', {
    schema: {
      tags: ['Intelligence'],
      summary: 'Perform comprehensive vault security audit',
      description: 'Analyze password vault for security vulnerabilities, breaches, and recommendations',
      body: {
        type: 'object',
        properties: {
          requestId: { type: 'string', format: 'uuid' },
          passwords: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                site: { type: 'string' },
                username: { type: 'string' },
                password: { type: 'string' },
                lastUpdated: { type: 'string' },
                category: { type: 'string' },
                notes: { type: 'string' }
              },
              required: ['site', 'username', 'password']
            }
          },
          analysisDepth: { type: 'string', enum: ['basic', 'standard', 'comprehensive'] },
          includeBreachCheck: { type: 'boolean' },
          includeTrendAnalysis: { type: 'boolean' }
        },
        required: ['requestId', 'passwords']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                requestId: { type: 'string' },
                userId: { type: 'string' },
                timestamp: { type: 'string' },
                securityScore: { type: 'number' },
                riskLevel: { type: 'string', enum: ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'] },
                summary: { type: 'string' },
                recommendations: { type: 'array', items: { type: 'string' } }
              }
            }
          }
        }
      }
    }
  }, async (request: FastifyRequest<{ Body: VaultAuditRequest }>, reply: FastifyReply) => {
    const startTime = Date.now();
    
    try {
      // Validate request body
      const validatedRequest = VaultAuditRequestSchema.parse(request.body);
      const userId = request.user!.uid;

      // Check user limits and permissions
      const userData = await fastify.firebaseService.getUserData(userId);
      const tier = userData?.tier || 'free';
      
      // Apply tier-based limits
      if (tier === 'free' && validatedRequest.passwords.length > 10) {
        return reply.code(403).send({
          success: false,
          error: {
            code: 'TIER_LIMIT_EXCEEDED',
            message: 'Free tier limited to 10 passwords per audit. Upgrade for more.',
            details: { limit: 10, requested: validatedRequest.passwords.length }
          }
        });
      }

      // Prepare audit request with user context
      const auditRequest: VaultAuditRequest = {
        ...validatedRequest,
        userId
      };

      fastify.log.info(`Starting vault audit for user ${userId} with ${validatedRequest.passwords.length} passwords`);

      // Execute AI-powered audit using Eko
      const auditResult = await fastify.ekoService.auditVault(auditRequest);

      // Save audit result to database
      await fastify.firebaseService.saveAuditResult(userId, auditResult);

      const processingTime = Date.now() - startTime;

      const response: APIResponse<VaultAuditResult> = {
        success: true,
        data: auditResult,
        meta: {
          requestId: validatedRequest.requestId,
          timestamp: new Date().toISOString(),
          processingTime,
          rateLimit: {
            remaining: userData?.limits?.auditsPerMonth - 1 || 49,
            resetTime: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          }
        }
      };

      fastify.log.info(`Vault audit completed for user ${userId} in ${processingTime}ms, score: ${auditResult.securityScore}`);
      
      return reply.send(response);

    } catch (error) {
      fastify.log.error('Vault audit failed:', error);
      
      return reply.code(500).send({
        success: false,
        error: {
          code: 'AUDIT_FAILED',
          message: error instanceof z.ZodError ? 'Invalid request data' : 'Audit processing failed',
          details: error instanceof z.ZodError ? error.errors : undefined
        },
        meta: {
          requestId: request.body?.requestId || 'unknown',
          timestamp: new Date().toISOString(),
          processingTime: Date.now() - startTime
        }
      });
    }
  });

  // Phishing URL Check
  fastify.post<{ Body: PhishingCheckRequest }>('/phishing-check', {
    schema: {
      tags: ['Intelligence'],
      summary: 'Check URL for phishing and security risks',
      description: 'Analyze URL/domain for potential phishing, malware, and security threats',
      body: {
        type: 'object',
        properties: {
          requestId: { type: 'string', format: 'uuid' },
          url: { type: 'string', format: 'uri' },
          context: { type: 'string' },
          userAgent: { type: 'string' },
          referrer: { type: 'string' }
        },
        required: ['requestId', 'url']
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'object',
              properties: {
                requestId: { type: 'string' },
                url: { type: 'string' },
                timestamp: { type: 'string' },
                riskLevel: { type: 'string', enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] },
                isPhishing: { type: 'boolean' },
                confidence: { type: 'number' },
                recommendation: { type: 'string' }
              }
            }
          }
        }
      }
    }
  }, async (request: FastifyRequest<{ Body: PhishingCheckRequest }>, reply: FastifyReply) => {
    const startTime = Date.now();
    
    try {
      const validatedRequest = PhishingCheckRequestSchema.parse(request.body);
      const userId = request.user!.uid;

      fastify.log.info(`Checking URL for phishing: ${validatedRequest.url} for user ${userId}`);

      // Execute AI-powered phishing check using Eko
      const checkResult = await fastify.ekoService.checkPhishing(validatedRequest);

      const processingTime = Date.now() - startTime;

      const response: APIResponse<PhishingCheckResult> = {
        success: true,
        data: checkResult,
        meta: {
          requestId: validatedRequest.requestId,
          timestamp: new Date().toISOString(),
          processingTime
        }
      };

      fastify.log.info(`Phishing check completed for ${validatedRequest.url}: ${checkResult.riskLevel} risk`);
      
      return reply.send(response);

    } catch (error) {
      fastify.log.error('Phishing check failed:', error);
      
      return reply.code(500).send({
        success: false,
        error: {
          code: 'PHISHING_CHECK_FAILED',
          message: error instanceof z.ZodError ? 'Invalid request data' : 'Phishing check failed',
          details: error instanceof z.ZodError ? error.errors : undefined
        },
        meta: {
          requestId: request.body?.requestId || 'unknown',
          timestamp: new Date().toISOString(),
          processingTime: Date.now() - startTime
        }
      });
    }
  });

  // Password Rotation Planning
  fastify.post<{ Body: RotationPlanRequest }>('/rotation-plan', {
    schema: {
      tags: ['Intelligence'],
      summary: 'Generate intelligent password rotation plan',
      description: 'Create AI-optimized password rotation schedule based on security priorities',
      body: {
        type: 'object',
        properties: {
          requestId: { type: 'string', format: 'uuid' },
          passwords: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string' },
                site: { type: 'string' },
                username: { type: 'string' },
                password: { type: 'string' },
                lastUpdated: { type: 'string' }
              },
              required: ['site', 'username', 'password']
            }
          },
          prioritySites: { type: 'array', items: { type: 'string' } },
          rotationFrequency: { type: 'string', enum: ['weekly', 'monthly', 'quarterly', 'annual'] },
          userPreferences: {
            type: 'object',
            properties: {
              maxPasswordsPerWeek: { type: 'number' },
              preferredDays: { type: 'array', items: { type: 'string' } },
              avoidBusyPeriods: { type: 'boolean' },
              reminderPreference: { type: 'string', enum: ['email', 'push', 'sms', 'none'] },
              autoRotateWhenPossible: { type: 'boolean' }
            }
          }
        },
        required: ['requestId', 'passwords']
      }
    }
  }, async (request: FastifyRequest<{ Body: RotationPlanRequest }>, reply: FastifyReply) => {
    const startTime = Date.now();
    
    try {
      const validatedRequest = RotationPlanRequestSchema.parse(request.body);
      const userId = request.user!.uid;

      // Check if user has access to rotation planning (Pro+ feature)
      const userData = await fastify.firebaseService.getUserData(userId);
      const tier = userData?.tier || 'free';
      
      if (!['pro', 'family', 'enterprise'].includes(tier)) {
        return reply.code(403).send({
          success: false,
          error: {
            code: 'FEATURE_NOT_AVAILABLE',
            message: 'Password rotation planning requires Pro tier or higher',
            details: { currentTier: tier, requiredTier: 'pro' }
          }
        });
      }

      const rotationRequest: RotationPlanRequest = {
        ...validatedRequest,
        userId
      };

      fastify.log.info(`Generating rotation plan for user ${userId} with ${validatedRequest.passwords.length} passwords`);

      // Execute AI-powered rotation planning using Eko
      const rotationPlan = await fastify.ekoService.createRotationPlan(rotationRequest);

      const processingTime = Date.now() - startTime;

      const response: APIResponse<RotationPlanResult> = {
        success: true,
        data: rotationPlan,
        meta: {
          requestId: validatedRequest.requestId,
          timestamp: new Date().toISOString(),
          processingTime
        }
      };

      fastify.log.info(`Rotation plan generated for user ${userId}: ${rotationPlan.totalPasswords} passwords, ${rotationPlan.estimatedTimeRequired} hours estimated`);
      
      return reply.send(response);

    } catch (error) {
      fastify.log.error('Rotation plan generation failed:', error);
      
      return reply.code(500).send({
        success: false,
        error: {
          code: 'ROTATION_PLAN_FAILED',
          message: error instanceof z.ZodError ? 'Invalid request data' : 'Rotation plan generation failed',
          details: error instanceof z.ZodError ? error.errors : undefined
        },
        meta: {
          requestId: request.body?.requestId || 'unknown',
          timestamp: new Date().toISOString(),
          processingTime: Date.now() - startTime
        }
      });
    }
  });

  // Get Audit History
  fastify.get('/audit-history', {
    schema: {
      tags: ['Intelligence'],
      summary: 'Get user audit history',
      description: 'Retrieve historical audit results for trend analysis',
      querystring: {
        type: 'object',
        properties: {
          limit: { type: 'number', minimum: 1, maximum: 50, default: 10 },
          offset: { type: 'number', minimum: 0, default: 0 }
        }
      },
      response: {
        200: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            data: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: { type: 'string' },
                  timestamp: { type: 'string' },
                  securityScore: { type: 'number' },
                  totalPasswords: { type: 'number' },
                  riskLevel: { type: 'string' }
                }
              }
            }
          }
        }
      }
    }
  }, async (request: FastifyRequest<{ Querystring: { limit?: number; offset?: number } }>, reply: FastifyReply) => {
    try {
      const userId = request.user!.uid;
      const { limit = 10 } = request.query;

      const auditHistory = await fastify.firebaseService.getAuditHistory(userId, limit);

      return reply.send({
        success: true,
        data: auditHistory,
        meta: {
          requestId: `history-${Date.now()}`,
          timestamp: new Date().toISOString(),
          processingTime: 0
        }
      });

    } catch (error) {
      fastify.log.error('Failed to fetch audit history:', error);
      
      return reply.code(500).send({
        success: false,
        error: {
          code: 'HISTORY_FETCH_FAILED',
          message: 'Failed to retrieve audit history'
        }
      });
    }
  });

  // Security Report Generation
  fastify.post('/generate-report', {
    schema: {
      tags: ['Intelligence'],
      summary: 'Generate formatted security report',
      description: 'Create executive, technical, or user-friendly security reports',
      body: {
        type: 'object',
        properties: {
          auditId: { type: 'string' },
          format: { type: 'string', enum: ['executive', 'technical', 'user-friendly'] },
          includeCharts: { type: 'boolean', default: false }
        },
        required: ['auditId', 'format']
      }
    }
  }, async (request: FastifyRequest<{ Body: { auditId: string; format: string; includeCharts?: boolean } }>, reply: FastifyReply) => {
    const startTime = Date.now();
    
    try {
      const { auditId, format, includeCharts = false } = request.body;
      const userId = request.user!.uid;

      // This would typically fetch audit data and format it
      // For now, return a success response
      const mockReport = {
        title: `${format.charAt(0).toUpperCase() + format.slice(1)} Security Report`,
        generatedAt: new Date().toISOString(),
        userId,
        auditId,
        content: `This is a ${format} security report generated for audit ${auditId}`
      };

      return reply.send({
        success: true,
        data: mockReport,
        meta: {
          requestId: `report-${Date.now()}`,
          timestamp: new Date().toISOString(),
          processingTime: Date.now() - startTime
        }
      });

    } catch (error) {
      fastify.log.error('Report generation failed:', error);
      
      return reply.code(500).send({
        success: false,
        error: {
          code: 'REPORT_GENERATION_FAILED',
          message: 'Failed to generate security report'
        }
      });
    }
  });
};

export { intelligenceRoutes };
