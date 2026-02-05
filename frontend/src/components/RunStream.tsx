import { Loader2, RefreshCw, FileCode, Terminal, Brain, Zap, Network } from 'lucide-react'
import { LogEntry } from '../types'
import { PhysicsVisualizer } from './PhysicsVisualizer'

interface RunStreamProps {
  selectedRun: any;
  isLoading: boolean;
  onRerun: () => void;
}

export function RunStream({ selectedRun, isLoading, onRerun }: RunStreamProps) {

  if (!selectedRun) return null

  // Helper to distinguish log types
  const getLogStyle = (step: string) => {
      const lowerStep = step.toLowerCase();
      
      if (['planner', 'analysis', 'strategy', 'review', 'critic'].some(k => lowerStep.includes(k))) {
          return {
              containerClass: "bg-slate-900/40 border-slate-800/60 border-dashed",
              iconColor: "text-slate-500",
              badgeClass: "bg-slate-800 text-slate-400",
              typeIcon: <Brain className="w-3 h-3" />
          }
      }
      
      if (['abn', 'connect', 'propose', 'receive', 'negotiate'].some(k => lowerStep.includes(k))) {
          return {
              containerClass: "bg-indigo-950/20 border-indigo-500/30",
              iconColor: "text-indigo-400",
              badgeClass: "bg-indigo-900/40 text-indigo-300 border border-indigo-500/20",
              typeIcon: <Network className="w-3 h-3" />
          }
      }
      
      return {
          containerClass: "bg-slate-900/80 border-slate-700",
          iconColor: "text-beam-400",
          badgeClass: "bg-beam-900/30 text-beam-300 border border-beam-500/20",
          typeIcon: <Zap className="w-3 h-3" />
      }
  }

  // Helper to detect Physics JSON
  const getPhysicsData = (stdout: string) => {
      if (!stdout) return null;
      try {
          const data = JSON.parse(stdout);
          // Check signature keys for Physics Agent
          if (data.analysis && data.final_answer && data.steps && data.analysis.knowns) {
              console.log("Physics Visualizer: Valid Data Detected", data);
              return data;
          }
      } catch (e) {
          // Silent fail for normal text output
          return null;
      }
      return null;
  }

  const logs = selectedRun.payload?.trace_log ? [...selectedRun.payload.trace_log].reverse() : [];
  const physicsData = selectedRun.payload?.execution_result?.stdout 
      ? getPhysicsData(selectedRun.payload.execution_result.stdout) 
      : null;

  return (
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
          
          {/* Header Card */}
          <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                  <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                      {selectedRun.summary || "Mission Log"}
                  </h2>
                  <p className="text-slate-500 text-sm font-mono">ID: {selectedRun.run_id}</p>
              </div>
              <div className="flex items-center gap-3">
                  {selectedRun.problem_description && (
                      <button 
                          onClick={onRerun}
                          disabled={isLoading}
                          className="flex items-center gap-2 text-white bg-blue-600 hover:bg-blue-500 transition-colors text-sm px-4 py-2 rounded-lg font-bold shadow-lg shadow-blue-900/20"
                      >
                          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                          Rerun
                      </button>
                  )}
                  
                  {selectedRun.payload?.code_url && (
                     <a href={selectedRun.payload.code_url} target="_blank" className="flex items-center gap-2 text-beam-400 hover:text-white transition-colors text-sm border border-beam-900 bg-beam-900/20 px-4 py-2 rounded-lg hover:bg-beam-900/40">
                         <FileCode className="w-4 h-4" /> View Source Code
                     </a>
                  )}
              </div>
          </div>

          {/* OUTPUT VISUALIZATION */}
          {physicsData ? (
              <PhysicsVisualizer data={physicsData} />
          ) : (
              // Standard Terminal Output
              selectedRun.payload?.execution_result && (
                  <div className="bg-black rounded-xl border border-slate-800 overflow-hidden font-mono text-sm shadow-2xl ring-1 ring-white/5">
                      <div className="bg-slate-900/50 px-4 py-2 flex items-center gap-2 border-b border-slate-800">
                          <Terminal className="w-4 h-4 text-slate-500" />
                          <span className="text-slate-500 font-bold uppercase tracking-wider text-xs">Final Output</span>
                      </div>
                      <div className="p-6 text-green-400 whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                          {selectedRun.payload.execution_result.stdout 
                            ? selectedRun.payload.execution_result.stdout 
                            : (selectedRun.payload.execution_result.error 
                                ? `Error: ${selectedRun.payload.execution_result.error}`
                                : "No standard output captured.")}
                      </div>
                      {selectedRun.payload.execution_result.stderr && (
                          <div className="p-6 border-t border-red-900/30 text-red-400 whitespace-pre-wrap bg-red-900/5">
                              {selectedRun.payload.execution_result.stderr}
                          </div>
                      )}
                  </div>
              )
          )}

          {/* AGENT THOUGHT STREAM */}
          <div className="relative pl-8 space-y-6 before:absolute before:left-3.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-slate-800 before:to-slate-800/0 before:border-l before:border-slate-800 before:border-dashed">
              {logs.map((log: LogEntry, i: number) => {
                  const style = getLogStyle(log.step);
                  
                  return (
                  <div key={i} className="relative animate-in fade-in slide-in-from-top-4 duration-500" style={{animationDelay: `${i * 50}ms`}}>
                      <div className={`absolute -left-8 top-0 w-8 h-8 bg-slate-950 border border-slate-800 rounded-full flex items-center justify-center text-lg shadow-lg z-10 ring-4 ring-slate-950 ${style.iconColor}`}>
                          {log.icon}
                      </div>
                      
                      <div className={`${style.containerClass} rounded-xl p-4 transition-colors duration-200 shadow-sm group border`}>
                          <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                  <span className={`font-bold text-xs uppercase tracking-widest ${style.iconColor}`}>{log.agent}</span>
                                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono flex items-center gap-1 ${style.badgeClass}`}>
                                      {style.typeIcon}
                                      {log.step}
                                  </span>
                              </div>
                              <span className="text-slate-600 text-xs font-mono">{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                          </div>
                          <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-mono opacity-90 group-hover:opacity-100 group-hover:text-slate-200 transition-opacity">
                              {log.content}
                          </div>
                      </div>
                  </div>
              )})}
              
              {logs.length === 0 && (
                  <div className="text-slate-600 italic text-sm">Waiting for agent activity...</div>
              )}
          </div>

      </div>
  )
}
