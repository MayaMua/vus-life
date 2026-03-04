import React from 'react';
import { Plus, Layout, Clock } from 'lucide-react';
import { SidePanel, SidePanelNav } from '../../../components/SidePanel';

export type ParserState = 'upload' | 'list' | 'preview';

interface LeftPanelProps {
  view: ParserState;
  setView: (view: ParserState) => void;
}

export const LeftPanel: React.FC<LeftPanelProps> = ({ view, setView }) => {
  return (
    <SidePanel variant="narrow" className="bg-[#f9fafb]">
      <div className="p-6 border-b border-slate-100 mb-4 shrink-0">
        <button 
          onClick={() => setView('upload')}
          className="w-full flex items-center justify-center gap-2 bg-white border border-blue-200 text-blue-600 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-50 transition-all shadow-sm active:scale-95"
        >
          <Plus className="w-4 h-4" />
          Create Task
        </button>
      </div>

      <SidePanelNav 
        items={[
          { id: 'list', label: 'Tasks', icon: Layout },
          { id: 'collections', label: 'My Collections', icon: Clock }
        ]}
        activeId={view === 'list' ? 'list' : ''}
        onSelect={(id) => {
           if (id === 'list') setView('list');
        }}
      />
    </SidePanel>
  );
};
