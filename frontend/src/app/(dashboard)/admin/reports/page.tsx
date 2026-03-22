"use client";

import { DownloadCloud, FileText, Table } from "lucide-react";
import { useState } from "react";

export default function ReportsPage() {
  const [downloading, setDownloading] = useState<string | null>(null);

  const handleDownload = async (type: 'pdf' | 'excel') => {
    try {
      setDownloading(type);
      const res = await fetch(`http://localhost:5000/api/reports/download/${type}`);
      
      if (!res.ok) throw new Error("Failed to download");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reports.${type === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error(error);
      alert("Download failed. Please try again later.");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Reports</h1>
        <p className="text-gray-500 mt-2">
          Download detailed summaries of data ingestion jobs and system activity.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
        
        {/* PDF Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="h-12 w-12 bg-red-100 text-red-600 rounded-lg flex items-center justify-center mb-4">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-semibold mb-2 text-gray-900">PDF Summary Report</h3>
          <p className="text-gray-500 text-sm mb-6">
            A human-readable document containing recent job statistics, process rates, and conflict logs.
          </p>
          <button 
            onClick={() => handleDownload('pdf')}
            disabled={!!downloading}
            className="w-full flex justify-center items-center px-4 py-2 border border-red-600 text-red-600 rounded hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            {downloading === 'pdf' ? (
              <span className="animate-pulse">Generating...</span>
            ) : (
              <>
                <DownloadCloud className="h-4 w-4 mr-2" />
                 Download PDF
              </>
            )}
          </button>
        </div>

        {/* Excel Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
          <div className="h-12 w-12 bg-green-100 text-green-700 rounded-lg flex items-center justify-center mb-4">
            <Table className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-semibold mb-2 text-gray-900">Excel Data Dump</h3>
          <p className="text-gray-500 text-sm mb-6">
            Raw export of all job histories and statistics in a spreadsheet format for further analysis.
          </p>
          <button 
            onClick={() => handleDownload('excel')}
            disabled={!!downloading}
            className="w-full flex justify-center items-center px-4 py-2 border border-green-600 text-green-700 rounded hover:bg-green-50 transition-colors disabled:opacity-50"
          >
            {downloading === 'excel' ? (
              <span className="animate-pulse">Generating...</span>
            ) : (
              <>
                <DownloadCloud className="h-4 w-4 mr-2" />
                 Download Excel
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  );
}
