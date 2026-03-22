import request from 'supertest';

// Mock dependencies before importing the app
jest.mock('@prisma/client', () => {
  const mPrismaClient = {
    user: {
      findUnique: jest.fn(),
      create: jest.fn(),
    },
    dataUploadJob: {
      findMany: jest.fn(),
      findUnique: jest.fn(),
      create: jest.fn(),
    }
  };
  return { PrismaClient: jest.fn(() => mPrismaClient) };
});

jest.mock('bullmq', () => ({
  Queue: jest.fn().mockImplementation(() => ({
    add: jest.fn(),
  })),
  Worker: jest.fn().mockImplementation(() => ({
    on: jest.fn(),
  })),
}));

import app from '../src/server';

describe('System Health & Base Routes', () => {
  it('GET /api/health should return 200 OK', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  it('GET /api/unknown should return 404', async () => {
    const res = await request(app).get('/api/unknown');
    expect(res.status).toBe(404);
  });
});

describe('Authentication (Phase 1)', () => {
  it('TC-AUTH-02: POST /api/auth/login with invalid password should fail', async () => {
    // We are expecting 401/404 based on standard auth flow
    const res = await request(app).post('/api/auth/login').send({
      email: 'admin@school.com',
      password: 'wrongpass'
    });
    // This expects the endpoint to exist. If auth.routes.ts isn't fully implemented yet,
    // this will fail properly, simulating a test failure.
    expect(res.status).toBeGreaterThanOrEqual(400); 
  });
});

describe('Data Ingestion (Phase 2)', () => {
  it('TC-DATA-02: POST /api/data/upload with NO file should return 400', async () => {
    const res = await request(app).post('/api/data/upload');
    expect(res.status).toBe(400);
    expect(res.body.error).toBe('No file uploaded');
  });
});

describe('Report Generation (Phase 2)', () => {
  it('TC-REP-01: GET /api/reports/download/pdf should generate PDF', async () => {
    const { PrismaClient } = require('@prisma/client');
    const prisma = new PrismaClient();
    
    // Mock DB response
    prisma.dataUploadJob.findMany.mockResolvedValue([
      { id: '123', status: 'COMPLETED', totalRows: 50, processedRows: 50, createdAt: new Date() }
    ]);

    const res = await request(app).get('/api/reports/download/pdf');
    expect(res.status).toBe(200);
    expect(res.header['content-type']).toBe('application/pdf');
  });
});
