import Fastify from 'fastify';
import cors from '@fastify/cors';
import helmet from '@fastify/helmet';
import rateLimit from '@fastify/rate-limit';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';
import dotenv from 'dotenv';

import { EkoService } from './services/EkoService.js';
import { FirebaseService } from './services/FirebaseService.js';
import { intelligenceRoutes } from './routes/intelligence.js';
import { healthRoutes } from './routes/health.js';
import type { FastifyRequest } from 'fastify';

// Load environment variables
dotenv.config();

const server = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: process.env.NODE_ENV === 'development' ? {
      target: 'pino-pretty',
      options: {
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname',
      },
    } : undefined,
  },
});

// Type augmentation for Fastify instance
declare module 'fastify' {
  interface FastifyInstance {
    ekoService: EkoService;
    firebaseService: FirebaseService;
  }
  interface FastifyRequest {
    user?: {
      uid: string;
      email?: string;
    };
  }
}

async function build() {
  try {
    // Security plugins
    await server.register(helmet, {
      contentSecurityPolicy: false, // Allow for development
    });

    await server.register(cors, {
      origin: process.env.NODE_ENV === 'development' 
        ? ['http://localhost:8081', 'exp://192.168.1.100:8081'] // Expo dev server
        : ['https://your-production-domain.com'],
      credentials: true,
    });

    await server.register(rateLimit, {
      max: parseInt(process.env.RATE_LIMIT_MAX || '100'),
      timeWindow: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000'),
    });

    // API Documentation
    await server.register(swagger, {
      swagger: {
        info: {
          title: 'SuperPassword AI Service',
          description: 'Eko-powered AI intelligence for password management',
          version: '1.0.0',
        },
        host: `localhost:${process.env.PORT || 3001}`,
        schemes: ['http', 'https'],
        consumes: ['application/json'],
        produces: ['application/json'],
        tags: [
          { name: 'Intelligence', description: 'AI-powered security intelligence' },
          { name: 'Health', description: 'Service health and status' },
        ],
      },
    });

    await server.register(swaggerUi, {
      routePrefix: '/docs',
      uiConfig: {
        docExpansion: 'list',
        deepLinking: false,
      },
    });

    // Initialize services
    const firebaseService = new FirebaseService();
    const ekoService = new EkoService();
    
    server.decorate('firebaseService', firebaseService);
    server.decorate('ekoService', ekoService);

    // Authentication middleware
    server.addHook('preHandler', async (request: FastifyRequest, reply) => {
      // Skip auth for health and docs endpoints
      if (request.url.startsWith('/health') || request.url.startsWith('/docs')) {
        return;
      }

      const authHeader = request.headers.authorization;
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return reply.code(401).send({ error: 'Missing or invalid authorization header' });
      }

      const token = authHeader.substring(7);
      try {
        const decodedToken = await firebaseService.verifyToken(token);
        request.user = {
          uid: decodedToken.uid,
          email: decodedToken.email,
        };
      } catch (error) {
        server.log.error('Token verification failed:', error);
        return reply.code(401).send({ error: 'Invalid authentication token' });
      }
    });

    // Register routes
    await server.register(healthRoutes, { prefix: '/health' });
    await server.register(intelligenceRoutes, { prefix: `/api/${process.env.API_VERSION || 'v1'}/intelligence` });

    return server;
  } catch (err) {
    server.log.error('Error building server:', err);
    throw err;
  }
}

async function start() {
  try {
    const server = await build();
    const port = parseInt(process.env.PORT || '3001');
    const host = process.env.HOST || '0.0.0.0';
    
    await server.listen({ port, host });
    server.log.info(`🚀 SuperPassword AI Service running on http://${host}:${port}`);
    server.log.info(`📚 API Documentation available at http://${host}:${port}/docs`);
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\\nReceived SIGINT, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\\nReceived SIGTERM, shutting down gracefully...');
  process.exit(0);
});

if (import.meta.url === `file://${process.argv[1]}`) {
  start();
}

export { build };
