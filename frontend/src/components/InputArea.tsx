import { Brain, ArrowRight, Loader2, Activity, Play } from 'lucide-react'

interface InputAreaProps {
  prompt: string;
  setPrompt: (prompt: string) => void;
  isLoading: boolean;
  onStart: () => void;
  result: any;
  formInputs: Record<string, any>;
  onInputChange: (name: string, value: string) => void;
  onContinue: () => void;
  error: string | null;
}

export function InputArea({
  prompt,
  setPrompt,
  isLoading,
  onStart,
  result,
  onInputChange,
  onContinue,
  error
}: InputAreaProps) {
  
  // 1. INPUT AREA (Only if no active run and no result needing clarification)
  if (!result) {
    return (
        <div className="max-w-2xl mx-auto mt-12 sm:mt-24 space-y-6 animate-in fade-in slide-in-from-bottom-8">
            <div className="text-center space-y-2">
                <Brain className="w-16 h-16 text-beam-500 mx-auto mb-6 drop-shadow-lg" />
                <h2 className="text-4xl font-extrabold tracking-tight">What are we building?</h2>
                <p className="text-lg text-slate-400">Describe a simulation, calculation, or engineering problem.</p>
            </div>
            
            <div className="relative group">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Calculate the stress in a steel beam with 500N load..."
                className="w-full h-40 bg-slate-900 border-2 border-slate-800 rounded-xl p-6 text-lg text-white placeholder-slate-600 focus:border-beam-600 focus:ring-0 transition-colors resize-none shadow-2xl"
                disabled={isLoading}
              />
              <button 
                onClick={onStart}
                disabled={!prompt.trim() || isLoading}
                className="absolute bottom-4 right-4 bg-beam-600 hover:bg-beam-500 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-bold shadow-lg flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
              >
                 {isLoading ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                 Initialize
              </button>
            </div>
            {error && <div className="text-red-400 text-center bg-red-900/20 p-2 rounded border border-red-900/50">{error}</div>}
        </div>
    )
  }

  // 2. FORM INTERFACE (If Awaiting User)
  if (result.state === "AWAITING_USER") {
    return (
        <div className="max-w-2xl mx-auto mt-10 p-8 bg-slate-900/80 backdrop-blur border border-beam-500/30 rounded-2xl shadow-2xl animate-in fade-in zoom-in-95">
             <h2 className="text-2xl font-bold text-white flex items-center gap-3 mb-2">
                  <Activity className="text-beam-500 w-6 h-6" />
                  Clarification Needed
              </h2>
              <p className="text-slate-400 mb-8 ml-9">The swarm has analyzed your request but needs specific variables to proceed.</p>
              
              <div className="space-y-6">
                  {result.payload.missing_vars.map((variable: any) => (
                      <div key={variable.name} className="space-y-2">
                          <label className="block text-sm font-bold text-beam-300 ml-1">
                              {variable.description}
                          </label>
                          <input 
                              type={variable.type === "number" ? "number" : "text"}
                              placeholder={`e.g. ${variable.default || ''}`}
                              className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 text-white focus:border-beam-500 focus:ring-1 focus:ring-beam-500 transition-all outline-none"
                              onChange={(e) => onInputChange(variable.name, e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && onContinue()}
                          />
                      </div>
                  ))}
              </div>

              {error && <div className="text-red-400 mt-4 text-sm bg-red-900/20 p-2 rounded">{error}</div>}

              <div className="flex justify-end gap-3 mt-8">
                  <button 
                      onClick={onContinue}
                      disabled={isLoading}
                      className="bg-beam-600 hover:bg-beam-500 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 shadow-lg hover:shadow-beam-900/40 transition-all transform hover:-translate-y-0.5"
                  >
                      {isLoading ? <Loader2 className="animate-spin" /> : <Play className="w-4 h-4" />}
                      Execute Simulation
                  </button>
              </div>
        </div>
    )
  }

  return null
}
