import React from 'react';
import { FileText } from 'lucide-react';

interface PageSelectorProps {
  selectedFile: File | null;
  pageSelection: string;
  setPageSelection: (val: string) => void;
  onRun: () => void;
}

export const PageSelector: React.FC<PageSelectorProps> = ({
  selectedFile,
  pageSelection,
  setPageSelection,
  onRun
}) => {
  if (!selectedFile) return null;

  const isPdf = selectedFile.type === 'application/pdf';

  return (
    <div className="w-full mt-6 bg-white border border-slate-200 rounded-xl p-5 shadow-sm shrink-0">
      <div className="flex items-center justify-between mb-3">
         <div className="flex items-center gap-2">
           <FileText className="w-4 h-4 text-blue-500" />
           <h3 className="text-sm font-bold text-slate-800">
             {isPdf ? 'Page Selection' : 'Image Processing'}
           </h3>
         </div>
         <button 
           onClick={onRun}
           className="px-5 py-1.5 bg-blue-600 text-white text-sm font-bold rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
         >
           Run
         </button>
      </div>
      <input 
         type="text" 
         value={pageSelection}
         onChange={(e) => setPageSelection(e.target.value)}
         disabled={!isPdf}
         placeholder={isPdf ? "e.g., 1, 2, 4 or 1, 3-5 or 3-5" : "All content will be processed (Images cannot be paginated)"}
         className={`w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-mono ${
           !isPdf ? 'opacity-60 cursor-not-allowed text-slate-400' : ''
         }`}
      />
      {isPdf && (
        <p className="text-xs text-slate-400 mt-2">Leave blank to process all pages. Formats: '1, 2, 4' or '1, 3-5' or '3-5'.</p>
      )}
    </div>
  );
};
