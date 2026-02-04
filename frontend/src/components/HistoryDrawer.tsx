import React from 'react'
import { Database, ChevronRight, Trash2 } from 'lucide-react'

interface HistoryDrawerProps {
  isDrawerOpen: boolean;
  setIsDrawerOpen: (open: boolean) => void;
  history: any[];
  selectedRun: any;
  onSelectHistoryItem: (item: any) => void;
  onDeleteHistory: (e: React.MouseEvent, runId: string) => void;
}

export function HistoryDrawer({
  isDrawerOpen,
  setIsDrawerOpen,
  history,
  selectedRun,
  onSelectHistoryItem,
  onDeleteHistory
}: HistoryDrawerProps) {
  return (
    <>
      {/* SLIDING DRAWER (History) */}
      <div 
        className={`absolute inset-y-0 left-0 w-80 bg-slate-900/95 backdrop-blur border-r border-slate-800 transform transition-transform duration-300 ease-in-out z-40 flex flex-col ${isDrawerOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
          <div className="p-4 border-b border-slate-800 flex items-center gap-2 text-beam-400 font-bold">
              <Database className="w-4 h-4" /> Mission Log
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {history.map(item => (
                  <div 
                    key={item.run_id}
                    onClick={() => onSelectHistoryItem(item)}
                    className={`w-full text-left p-3 rounded text-xs transition-colors border group cursor-pointer relative ${selectedRun?.run_id === item.run_id ? 'bg-beam-900/20 border-beam-600 text-white' : 'hover:bg-slate-800 border-transparent text-slate-400'}`}
                  >
                      <div className="font-medium truncate group-hover:text-beam-300 transition-colors pr-6">{item.problem_description}</div>
                      <div className="mt-1 flex items-center justify-between opacity-50">
                          <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <button
                          onClick={(e) => onDeleteHistory(e, item.run_id)}
                          className="absolute top-2 right-2 p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-900/20 rounded-md transition-all opacity-0 group-hover:opacity-100"
                          title="Delete Mission"
                      >
                          <Trash2 className="w-3.5 h-3.5" />
                      </button>
                  </div>
              ))}
              {history.length === 0 && (
                  <div className="text-center text-slate-600 italic p-4 text-sm">
                      No missions recorded yet.
                  </div>
              )}
          </div>
      </div>

      {/* OVERLAY (Closes drawer) */}
      {isDrawerOpen && (
          <div 
              className="absolute inset-0 bg-black/50 z-30 backdrop-blur-sm"
              onClick={() => setIsDrawerOpen(false)}
          />
      )}
    </>
  )
}
