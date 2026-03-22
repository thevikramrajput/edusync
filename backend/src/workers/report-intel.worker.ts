import { Worker, Job } from 'bullmq';
import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export const dataUploadWorker = new Worker('data-upload-queue', async (job: Job) => {
  const { jobId, data } = job.data;
  
  try {
    await prisma.dataUploadJob.update({
      where: { id: jobId },
      data: { status: 'PROCESSING' }
    });

    logger.info(`Processing job ${jobId} with ${data.length} rows`);

    // Mock Report Intelligence Agent Processing:
    // In a real implementation, we'd pass data to an LLM like OpenAI to map columns.
    // Here, we simulate cleaning and mapping.
    
    let processedRows = 0;
    
    for (const row of data) {
      // Simulate checking for missing/bad data
      const hasMissingData = Object.values(row as any).some(v => v === undefined || v === '');
      
      if (hasMissingData) {
        await prisma.conflictLog.create({
          data: {
            jobId,
            rowData: row as any,
            suggestedFix: { note: "AI Agent: Missing field data detected in this row" },
            status: 'PENDING'
          }
        });
      }
      
      processedRows++;
      
      // Update progress periodically
      if (processedRows % 10 === 0) {
        await prisma.dataUploadJob.update({
          where: { id: jobId },
          data: { processedRows }
        });
      }
    }

    await prisma.dataUploadJob.update({
      where: { id: jobId },
      data: { 
        status: 'COMPLETED',
        processedRows 
      }
    });

    logger.info(`Job ${jobId} completed successfully`);
  } catch (error: any) {
    logger.error(`Job ${jobId} failed: ${error.message}`);
    await prisma.dataUploadJob.update({
      where: { id: jobId },
      data: { 
        status: 'FAILED',
        errorLog: error.message
      }
    });
    throw error;
  }
}, {
  connection: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
  }
});

dataUploadWorker.on('completed', (job) => {
  logger.info(`Worker completed job ${job.id}`);
});

dataUploadWorker.on('failed', (job, err) => {
  logger.error(`Worker failed job ${job?.id} with error: ${err.message}`);
});
