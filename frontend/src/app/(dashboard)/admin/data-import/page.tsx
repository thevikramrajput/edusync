"use client";

import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, File, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export default function DataImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv']
    },
    maxFiles: 1
  });

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:5000/api/data/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      setJobId(data.jobId);
    } catch (error) {
      console.error(error);
      alert("Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (jobId && jobStatus?.status !== 'COMPLETED' && jobStatus?.status !== 'FAILED') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`http://localhost:5000/api/data/jobs/${jobId}`);
          if (res.ok) {
            const data = await res.json();
            setJobStatus(data);
          }
        } catch (error) {
          console.error("Failed to fetch job status", error);
        }
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [jobId, jobStatus?.status]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Import Engine</h1>
        <p className="text-gray-500 mt-2">
          Upload Excel or CSV files. Our Intelligence Agent will map columns, clean data, and import records automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold mb-4">Upload File</h2>
          
          {!jobId && (
            <>
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors
                  ${isDragActive ? 'border-red-500 bg-red-50' : 'border-gray-300 hover:border-gray-400'}`}
              >
                <input {...getInputProps()} />
                <UploadCloud className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                {isDragActive ? (
                  <p className="text-red-600 font-medium">Drop the Excel/CSV file here...</p>
                ) : (
                  <p className="text-gray-600">
                    Drag & drop an Excel/CSV file here, or click to select
                  </p>
                )}
              </div>

              {file && (
                <div className="mt-4 p-4 border rounded bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center space-x-3 text-sm">
                    <File className="text-blue-500 h-5 w-5" />
                    <span className="font-medium text-gray-700">{file.name}</span>
                    <span className="text-gray-500">{(file.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button 
                    onClick={handleUpload}
                    disabled={uploading}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 flex items-center"
                  >
                    {uploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {uploading ? 'Uploading...' : 'Process File'}
                  </button>
                </div>
              )}
            </>
          )}

          {jobStatus && (
            <div className="mt-6 space-y-4">
              <h3 className="font-medium text-gray-900 flex items-center">
                Processing Status: 
                <span className={`ml-2 px-2 py-1 rounded text-xs font-bold
                  ${jobStatus.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 
                    jobStatus.status === 'FAILED' ? 'bg-red-100 text-red-800' : 
                    'bg-blue-100 text-blue-800'}`}>
                  {jobStatus.status}
                </span>
              </h3>
              
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-red-600 h-2.5 rounded-full transition-all duration-500" 
                  style={{ width: `${jobStatus.totalRows > 0 ? (jobStatus.processedRows / jobStatus.totalRows) * 100 : 0}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500 text-right">
                {jobStatus.processedRows} / {jobStatus.totalRows} rows processed
              </p>

              {jobStatus.status === 'COMPLETED' && (
                <button 
                  onClick={() => { setJobId(null); setJobStatus(null); setFile(null); }}
                  className="mt-4 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 text-sm"
                >
                  Upload Another File
                </button>
              )}
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Conflict Resolution</h2>
          <p className="text-sm text-gray-500 mb-4">
            Rows requiring manual intervention will appear here.
          </p>

          {jobStatus?.conflicts?.length > 0 ? (
            <div className="space-y-3">
              {jobStatus.conflicts.map((conflict: any, idx: number) => (
                <div key={idx} className="p-3 border border-yellow-200 bg-yellow-50 flex items-start space-x-3 rounded text-sm">
                  <AlertCircle className="text-yellow-600 h-5 w-5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-yellow-800">Review Required</h4>
                    <p className="text-yellow-700 mt-1">{conflict.suggestedFix?.note || "AI Agent flagged an issue"}</p>
                    <pre className="text-xs bg-white p-2 mt-2 rounded border border-yellow-100 overflow-x-auto">
                      {JSON.stringify(conflict.rowData, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          ) : (
             <div className="text-center py-10 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
               <CheckCircle2 className="mx-auto h-12 w-12 text-gray-300 mb-2" />
               <p>No conflicts detected</p>
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
