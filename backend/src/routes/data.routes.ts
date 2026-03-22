import { Router } from 'express';
import multer from 'multer';
import * as xlsx from 'xlsx';
import { Queue } from 'bullmq';
import { PrismaClient } from '@prisma/client';
import fs from 'fs';

const router = Router();
const prisma = new PrismaClient();

const uploadQueue = new Queue('data-upload-queue', {
  connection: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
  }
});

// Ensure upload directory exists
const uploadDir = 'uploads/';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const upload = multer({ dest: uploadDir });

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const workbook = xlsx.readFile(req.file.path);
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    const jsonData = xlsx.utils.sheet_to_json(sheet);

    const totalRows = jsonData.length;

    const jobRecord = await prisma.dataUploadJob.create({
      data: {
        status: 'PENDING',
        totalRows,
        fileUrl: req.file.path,
      }
    });

    await uploadQueue.add('process-data', {
      jobId: jobRecord.id,
      filePath: req.file.path,
      data: jsonData
    });

    res.status(202).json({
      message: 'File uploaded and queued for processing',
      jobId: jobRecord.id,
      totalRows
    });
  } catch (error) {
    console.error('Upload Error:', error);
    res.status(500).json({ error: 'Failed to process upload' });
  }
});

router.get('/jobs/:id', async (req, res) => {
  try {
    const job = await prisma.dataUploadJob.findUnique({
      where: { id: req.params.id },
      include: { conflicts: true }
    });

    if (!job) {
      return res.status(404).json({ error: 'Job not found' });
    }

    res.status(200).json(job);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch job status' });
  }
});

export default router;
