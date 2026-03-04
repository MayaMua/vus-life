import React, { useState } from 'react';
import { Upload } from 'lucide-react';

interface UploaderProps {
  onFileAccept: (file: File) => void;
}

export const Uploader: React.FC<UploaderProps> = ({ onFileAccept }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileAccept(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <label 
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`aspect-[21/9] border-2 border-dashed rounded-3xl flex flex-col items-center justify-center p-12 transition-all cursor-pointer group ${
        isDragging ? 'border-blue-500 bg-blue-50/50' : 'border-slate-200 bg-slate-50/50 hover:border-blue-400 hover:bg-blue-50/30'
      }`}
    >
      <input 
        type="file" 
        className="hidden" 
        accept="image/*,application/pdf"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            onFileAccept(e.target.files[0]);
          }
        }}
      />
      <div className="relative mb-6">
        <div className={`absolute inset-0 rounded-full scale-150 blur-xl transition-opacity ${isDragging ? 'bg-blue-200 opacity-100' : 'bg-blue-100 opacity-50 group-hover:opacity-100'}`} />
        <Upload className={`w-16 h-16 relative transition-colors ${isDragging ? 'text-blue-500' : 'text-slate-300 group-hover:text-blue-500'}`} />
      </div>
      <div className="flex gap-4">
        <div className="flex items-center gap-2 px-6 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold shadow-sm hover:shadow-md transition-all text-slate-700 pointer-events-none">
          <Upload className="w-4 h-4 text-blue-500" />
          Upload Document or Image
        </div>
      </div>
      <p className="mt-4 text-xs text-slate-400 text-center max-w-xs transition-colors group-hover:text-slate-500">
        Drag and drop your PDF or Image file here, or click to browse.
      </p>
    </label>
  );
};
