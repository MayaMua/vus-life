import React, { useState } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Clock, 
  ChevronLeft, 
  Trash2, 
  ExternalLink, 
  Layout, 
  Columns, 
  Search, 
  Filter,
  MoreVertical,
  Bell
} from 'lucide-react';
import { LeftPanel, ParserState } from './components/LeftPanel';
import { Uploader } from './components/Uploader';
import { PageSelector } from './components/PageSelector';

interface Task {
  id: string;
  name: string;
  size: string;
  status: 'Completed' | 'Processing';
  type: string;
  model: string;
  createdTime: string;
}

const MOCK_TASKS: Task[] = [
  { id: '1', name: 'AI-ML-RisksMitigation.pdf', size: '2.3MB', status: 'Completed', type: 'Document', model: 'MinerU VLM', createdTime: '2026/01/19 13:01' },
  { id: '2', name: 'One variant GeneDx 2022_Redacted.pdf', size: '959.8KB', status: 'Completed', type: 'Document', model: 'MinerU VLM', createdTime: '2026/01/19 12:59' },
  { id: '3', name: 'One variant GeneDx 2022_Redacted.pdf', size: '959.8KB', status: 'Completed', type: 'Processing', model: 'MinerU VLM', createdTime: '2026/01/16 16:14' },
];

export const PdfParserPage: React.FC = () => {
  const [view, setView] = useState<ParserState>('upload');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  
  // File upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pageSelection, setPageSelection] = useState('');

  const onFileAccept = (file: File) => {
    if (file.type.startsWith('image/') || file.type === 'application/pdf') {
      setSelectedFile(file);
      setPageSelection('');
      setSelectedTask(null);
      setView('preview');
    } else {
      alert("Only Image and PDF files are supported.");
    }
  };

  const handleTaskClick = (task: Task) => {
    setSelectedFile(null); // Clear selected file when viewing history
    setSelectedTask(task);
    setView('preview');
  };

  const handleRun = () => {
    console.log("Processing file:", selectedFile?.name, "pages:", pageSelection);
  };

  return (
    <div className="flex h-full bg-white text-slate-900 overflow-hidden">
      {/* SECONDARY SIDEBAR (For PDF context) */}
      <LeftPanel view={view} setView={setView} />

      {/* MODULE CONTENT */}
      <div className="flex-1 flex flex-col overflow-hidden bg-white">
        
        {/* HEADER */}
        <header className="h-16 border-b border-slate-100 flex items-center justify-between px-8 bg-white z-10">
          <div className="flex items-center gap-2">
            {view === 'preview' && (
              <button 
                onClick={() => setView('list')}
                className="mr-4 p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
            <h2 className="text-lg font-bold text-slate-800">
              {view === 'upload' && "Intelligent Extraction"}
              {view === 'list' && "All Tasks"}
              {view === 'preview' && (selectedFile ? selectedFile.name : selectedTask?.name)}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-semibold border border-indigo-100 gap-2">
              <Bell className="w-3.5 h-3.5" />
              Intelligent extraction is in beta testing
            </div>
            <button className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-auto">
          {/* STATE A: UPLOAD DASHBOARD */}
          {view === 'upload' && (
            <div className="h-full flex flex-col p-8">
              <div className="mb-8">
                <p className="text-slate-500 text-sm">Make document and web content AI-consumable</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                  <Uploader onFileAccept={onFileAccept} />

                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Layout className="w-4 h-4 text-blue-500" />
                      Examples
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      {[1, 2].map(i => (
                        <div key={i} className="border border-slate-100 rounded-2xl p-4 hover:shadow-md transition-shadow cursor-pointer group">
                          <div className="aspect-video bg-slate-100 rounded-lg mb-4 flex items-center justify-center">
                            <FileText className="w-10 h-10 text-slate-300" />
                          </div>
                          <p className="text-sm font-bold text-slate-700 mb-2">Molecular Structure Extraction</p>
                          <div className="flex gap-2">
                            <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded uppercase font-bold tracking-tight">VLM</span>
                            <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded uppercase font-bold tracking-tight">New</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-6">
                   <div className="bg-[#f9fafb] border border-slate-100 rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-slate-800">Recent Tasks</h3>
                        <button onClick={() => setView('list')} className="text-xs text-blue-600 font-semibold hover:text-blue-700">View All</button>
                      </div>
                      <div className="space-y-3">
                        {MOCK_TASKS.slice(0, 4).map(t => (
                          <div key={t.id} onClick={() => handleTaskClick(t)} className="flex items-start gap-3 p-3 bg-white border border-slate-100 rounded-xl hover:border-blue-200 hover:shadow-sm cursor-pointer transition-all group">
                            <FileText className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                            <div className="overflow-hidden flex-1">
                              <p className="text-sm font-semibold text-slate-700 truncate group-hover:text-blue-600 transition-colors">{t.name}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] text-slate-400">{t.size}</span>
                                <span className="text-slate-300 text-[10px]">•</span>
                                <span className="text-[10px] text-slate-400">{t.createdTime}</span>
                              </div>
                            </div>
                            <div className="flex flex-col items-end justify-between h-full gap-2 mt-0.5">
                               {t.status === 'Completed' ? (
                                 <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                               ) : (
                                 <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
                               )}
                            </div>
                          </div>
                        ))}
                      </div>
                   </div>
                </div>
              </div>
            </div>
          )}

          {/* STATE B: TASK LIST */}
          {view === 'list' && (
            <div className="p-8">
              <div className="flex items-center justify-between mb-8">
                <div className="relative w-96">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input 
                    placeholder="Please enter the task name"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                  />
                </div>
                <button className="flex items-center gap-2 px-6 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-semibold hover:bg-slate-50 transition-all">
                  <Filter className="w-4 h-4 text-slate-400" />
                  Filter
                </button>
              </div>

              <div className="border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Task Name</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Type</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Model</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Created Time</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest text-right">Operation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {MOCK_TASKS.map((t) => (
                      <tr key={t.id} onClick={() => handleTaskClick(t)} className="hover:bg-blue-50/30 cursor-pointer transition-colors group">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-red-500" />
                            <div>
                              <p className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors">{t.name}</p>
                              <p className="text-[10px] text-slate-400 font-medium">{t.size}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {t.status === 'Completed' ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            ) : (
                              <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
                            )}
                            <span className={`text-xs font-bold ${t.status === 'Completed' ? 'text-emerald-600' : 'text-amber-600'}`}>
                              {t.status}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-xs font-medium text-slate-600">{t.type}</td>
                        <td className="px-6 py-4 text-xs font-medium text-slate-600">{t.model}</td>
                        <td className="px-6 py-4 text-xs font-medium text-slate-600">{t.createdTime}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-blue-600 transition-colors">
                              <ExternalLink className="w-4 h-4" />
                            </button>
                            <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-red-500 transition-colors">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* STATE C: SPLIT-SCREEN WORKSPACE */}
          {view === 'preview' && (
            <div className="h-full flex overflow-hidden">
              <div className="flex-1 border-r border-slate-200 bg-slate-100 relative">
                <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white/80 backdrop-blur shadow-sm px-4 py-1.5 rounded-full text-xs font-bold text-slate-500 flex items-center gap-4">
                  <span>Original File</span>
                  <div className="flex items-center gap-2 px-2 border-l border-slate-200">
                    <button className="p-1 hover:bg-slate-100 rounded">-</button>
                    <span>1 / 2</span>
                    <button className="p-1 hover:bg-slate-100 rounded">+</button>
                  </div>
                  <button className="p-1 hover:bg-slate-100 rounded">63%</button>
                </div>
                <div className="h-full w-full flex flex-col p-6 items-center justify-center">
                   {/* Preview Content */}
                   <div className="w-full flex-1 max-h-full bg-white shadow-xl rounded-xl flex flex-col items-center justify-center relative overflow-hidden border border-slate-200">
                      {selectedFile ? (
                        selectedFile.type.startsWith('image/') ? (
                           <img src={URL.createObjectURL(selectedFile)} alt="Preview" className="max-w-full max-h-[90%] object-contain" />
                        ) : selectedFile.type === 'application/pdf' ? (
                           <embed 
                             src={`${URL.createObjectURL(selectedFile)}#toolbar=0`} 
                             type="application/pdf"
                             className="w-full h-full" 
                           />
                        ) : null
                      ) : selectedTask ? (
                         <div className="flex flex-col items-center text-slate-300 w-full h-full justify-center">
                            <FileText className="w-20 h-20 opacity-20 mb-4" />
                            <p className="text-sm font-bold opacity-30 uppercase tracking-widest text-center">{selectedTask.name}</p>
                         </div>
                      ) : (
                         <div className="flex flex-col items-center text-slate-300 w-full h-full justify-center">
                             <FileText className="w-20 h-20 opacity-20 mb-4" />
                             <p className="text-sm font-bold opacity-30 uppercase tracking-widest text-center">No Preview Available</p>
                         </div>
                      )}
                   </div>
                   
                   {/* PDF Page Selection / Action logic */}
                   <PageSelector 
                     selectedFile={selectedFile} 
                     pageSelection={pageSelection} 
                     setPageSelection={setPageSelection} 
                     onRun={handleRun}
                   />
                </div>
              </div>
              
              <div className="flex-1 bg-white flex flex-col">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex bg-slate-100 p-1 rounded-lg">
                    <button className="px-4 py-1 text-xs font-bold bg-white text-blue-600 rounded-md shadow-sm">Markdown</button>
                    <button className="px-4 py-1 text-xs font-bold text-slate-500">JSON</button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400">
                      <Columns className="w-4 h-4" />
                    </button>
                    <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400">
                      <Layout className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                 <div className="flex-1 p-8 overflow-y-auto">
                   <article className="prose prose-slate max-w-none">
                     <h1 className="text-3xl font-bold mb-6 text-slate-800">Extraction Results</h1>
                     <p className="text-slate-600 leading-relaxed mb-4">The following text was intelligently extracted and formatted as Markdown. Tables and diagrams have been preserved where possible.</p>
                     
                     <div className="bg-slate-50 border border-slate-100 rounded-xl p-6 min-h-[300px] flex items-center justify-center text-slate-400 text-sm">
                       No data extracted yet. Please run the intelligent extraction process.
                     </div>
                   </article>
                 </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};