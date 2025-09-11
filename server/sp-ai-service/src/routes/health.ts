import { FastifyInstance, FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';

const healthRoutes: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  // Basic health check
  fastify.get('/', {
    schema: {
      tags: ['Health'],
      summary: 'Basic health check',
      response: {
        200: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            timestamp: { type: 'string' },
            uptime: { type: 'number' },
            version: { type: 'string' }
          }
        }
      }
    }
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version || '1.0.0'
    };
  });

  // Detailed health check with dependencies
  fastify.get('/detailed', {
    schema: {
      tags: ['Health'],
      summary: 'Detailed health check including dependencies',
      response: {
        200: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            timestamp: { type: 'string' },
            uptime: { type: 'number' },
            version: { type: 'string' },
            dependencies: {
              type: 'object',
              properties: {
                ekoService: { type: 'string' },
                firebaseService: { type: 'string' },
                database: { type: 'string' },
                llmProviders: {
                  type: 'object',
                  additionalProperties: { type: 'string' }
                }
              }
            },
            system: {
              type: 'object',
              properties: {
                nodeVersion: { type: 'string' },
                platform: { type: 'string' },
                memoryUsage: {
                  type: 'object',
                  properties: {
                    rss: { type: 'number' },
                    heapTotal: { type: 'number' },
                    heapUsed: { type: 'number' },
                    external: { type: 'number' }
                  }
                }
              }
            }
          }
        }
      }
    }
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const startTime = Date.now();
    
    // Check service dependencies
    const dependencies = {
      ekoService: 'unknown',
      firebaseService: 'unknown',
      database: 'unknown',
      llmProviders: {} as Record<string, string>
    };

    try {
      // Check Eko service
      if (fastify.ekoService) {
        dependencies.ekoService = 'healthy';
      } else {
        dependencies.ekoService = 'not_initialized';
      }
    } catch (error) {
      dependencies.ekoService = 'error';
    }

    try {
      // Check Firebase service
      if (fastify.firebaseService) {
        await fastify.firebaseService.verifyToken('mock-token-for-health-check');
        dependencies.firebaseService = 'healthy';
      } else {
        dependencies.firebaseService = 'not_initialized';
      }
    } catch (error) {
      dependencies.firebaseService = process.env.NODE_ENV === 'development' ? 'mock_mode' : 'error';
    }

    // Check LLM providers
    if (process.env.ANTHROPIC_API_KEY) {
      dependencies.llmProviders.anthropic = 'configured';
    }
    if (process.env.OPENAI_API_KEY) {
      dependencies.llmProviders.openai = 'configured';
    }
    if (process.env.GOOGLE_AI_API_KEY) {
      dependencies.llmProviders.google = 'configured';
    }

    // System information
    const memoryUsage = process.memoryUsage();
    const system = {
      nodeVersion: process.version,
      platform: process.platform,
      memoryUsage: {
        rss: Math.round(memoryUsage.rss / 1024 / 1024), // MB
        heapTotal: Math.round(memoryUsage.heapTotal / 1024 / 1024), // MB
        heapUsed: Math.round(memoryUsage.heapUsed / 1024 / 1024), // MB
        external: Math.round(memoryUsage.external / 1024 / 1024) // MB
      }
    };

    // Determine overall status
    const hasErrors = Object.values(dependencies).some(status => 
      typeof status === 'string' ? status === 'error' : Object.values(status).some(s => s === 'error')
    );
    
    const overallStatus = hasErrors ? 'degraded' : 'healthy';
    
    const responseTime = Date.now() - startTime;

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version || '1.0.0',
      dependencies,
      system,
      responseTime
    };
  });

  // Readiness check (for Kubernetes/Docker)
  fastify.get('/ready', {
    schema: {
      tags: ['Health'],
      summary: 'Readiness check for container orchestration',
      response: {
        200: {
          type: 'object',
          properties: {
            ready: { type: 'boolean' },
            timestamp: { type: 'string' }
          }
        },
        503: {
          type: 'object',
          properties: {
            ready: { type: 'boolean' },
            timestamp: { type: 'string' },
            reason: { type: 'string' }
          }
        }
      }
    }
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    // Check if critical services are ready
    let isReady = true;
    let reason = '';

    try {
      // Check if Eko service is initialized
      if (!fastify.ekoService) {
        isReady = false;
        reason = 'EkoService not initialized';
      }

      // Check if at least one LLM provider is configured
      const hasLLMProvider = process.env.ANTHROPIC_API_KEY || 
                            process.env.OPENAI_API_KEY || 
                            process.env.GOOGLE_AI_API_KEY;
      
      if (!hasLLMProvider && process.env.NODE_ENV !== 'development') {
        isReady = false;
        reason = 'No LLM provider configured';
      }

    } catch (error) {
      isReady = false;
      reason = `Health check failed: ${error}`;
    }

    const response = {
      ready: isReady,
      timestamp: new Date().toISOString(),
      ...(reason && { reason })
    };

    return reply.code(isReady ? 200 : 503).send(response);
  });

  // Liveness check (for Kubernetes/Docker)
  fastify.get('/live', {
    schema: {
      tags: ['Health'],
      summary: 'Liveness check for container orchestration',
      response: {
        200: {
          type: 'object',
          properties: {
            alive: { type: 'boolean' },
            timestamp: { type: 'string' }
          }
        }
      }
    }
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    // Simple check to ensure the process is responsive
    return {
      alive: true,
      timestamp: new Date().toISOString()
    };
  });

  // Metrics endpoint (basic)
  fastify.get('/metrics', {
    schema: {
      tags: ['Health'],
      summary: 'Basic metrics for monitoring',
      response: {
        200: {
          type: 'object',
          properties: {
            timestamp: { type: 'string' },
            uptime: { type: 'number' },
            memory: {
              type: 'object',
              properties: {
                rss: { type: 'number' },
                heapUsed: { type: 'number' },
                heapTotal: { type: 'number' }
              }
            },
            cpu: {
              type: 'object',
              properties: {
                usage: { type: 'number' }
              }
            }
          }
        }
      }
    }
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const memoryUsage = process.memoryUsage();
    const cpuUsage = process.cpuUsage();
    
    return {
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: {
        rss: memoryUsage.rss,
        heapUsed: memoryUsage.heapUsed,
        heapTotal: memoryUsage.heapTotal
      },
      cpu: {
        usage: (cpuUsage.user + cpuUsage.system) / 1000 // Convert to milliseconds
      }
    };
  });
};

export { healthRoutes };
