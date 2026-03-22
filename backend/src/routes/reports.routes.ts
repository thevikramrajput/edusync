import { Router } from 'express';
import { PrismaClient } from '@prisma/client';
import * as xlsx from 'xlsx';
import PDFDocument from 'pdfkit';

const router = Router();
const prisma = new PrismaClient();

router.get('/download/:type', async (req, res) => {
  try {
    const { type } = req.params;
    
    // For demonstration, let's fetch all DataUploadJobs and their basic data
    const jobs = await prisma.dataUploadJob.findMany({
      orderBy: { createdAt: 'desc' },
      take: 10
    });

    if (type === 'excel') {
      const worksheet = xlsx.utils.json_to_sheet(jobs.map((job: any) => ({
        ID: job.id,
        Status: job.status,
        TotalRows: job.totalRows,
        ProcessedRows: job.processedRows,
        Date: job.createdAt.toISOString()
      })));
      
      const workbook = xlsx.utils.book_new();
      xlsx.utils.book_append_sheet(workbook, worksheet, 'Recent Jobs');
      
      const buffer = xlsx.write(workbook, { type: 'buffer', bookType: 'xlsx' });
      
      res.setHeader('Content-Disposition', 'attachment; filename="reports.xlsx"');
      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      return res.send(buffer);
    } 
    
    if (type === 'pdf') {
      const doc = new PDFDocument();
      
      res.setHeader('Content-Disposition', 'attachment; filename="reports.pdf"');
      res.setHeader('Content-Type', 'application/pdf');
      
      doc.pipe(res);
      
      doc.fontSize(20).text('RED School EduOS - Data Upload Report', { align: 'center' });
      doc.moveDown();
      
      jobs.forEach((job: any, index: number) => {
        doc.fontSize(12).text(`Job ${index + 1}: ${job.id}`);
        doc.fontSize(10).text(`Status: ${job.status} | Rows: ${job.processedRows}/${job.totalRows}`);
        doc.text(`Date: ${job.createdAt.toISOString()}`);
        doc.moveDown();
      });
      
      doc.end();
      return;
    }

    res.status(400).json({ error: 'Invalid report type. Use excel or pdf.' });
  } catch (error) {
    console.error('Report Generation Error:', error);
    res.status(500).json({ error: 'Failed to generate report' });
  }
});

export default router;
