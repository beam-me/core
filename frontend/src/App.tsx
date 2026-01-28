import { useState, useEffect, useRef } from 'react'
import { Sparkles, Loader2, ArrowRight, Terminal, FileCode, Brain, Activity, Database, Play, Menu, X, ChevronRight, Trash2, RefreshCw, Network, Cpu, Share2, ShieldCheck, Zap } from 'lucide-react'

// Types for our structured logs
interface LogEntry {
    agent: string;
    step: string;
    content: string;
    icon: string;
    timestamp: string;
}

interface AgentProfile {
    id: string;
    name: string;
    role: string;
    icon: string;
    description: string;
    instructions: string[];
    tools: string[];
    relationships: {
        incoming: string[];
        outgoing: string[];
    }
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<any[]>([])
  const [agents, setAgents] = useState<AgentProfile[]>([])
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null)
  
  // View Modes
  const [showSwarm, setShowSwarm] = useState(false)
  
  // Controls the "Mind of the Agent" view
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const streamEndRef = useRef<HTMLDivElement>(null)
  
  // Drawer State
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  
  const [formInputs, setFormInputs] = useState<Record<string, any>>({})

  // Fetch history to populate the "Past Sessions" sidebar or dropdown
  useEffect(() => {
    fetchHistory(true) // Auto-select on first load
    fetchAgents()
  }, [])

  // Auto-scroll the stream
  useEffect(() => {
    if (streamEndRef.current) {
        streamEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [selectedRun])

  const fetchHistory = async (autoSelect: boolean = false) => {
    try {
        const res = await fetch('/api/history')
        if (res.ok) {
            const data = await res.json()
            setHistory(data)
            
            if (autoSelect && !selectedRun && data.length > 0) {
               const recent = data[0]
               setSelectedRun({
                   run_id: recent.run_id,
                   state: "COMPLETED",
                   problem_description: recent.problem_description, 
                   summary: "Loaded from history",
                   payload: {
                       trace_log: recent.metadata?.trace_log || [],
                       code_url: recent.metadata?.url ? `https://github.com/beam-me/user-code/blob/main/${recent.file_path}` : null,
                       execution_result: { stdout: "Run execution to see live output." } 
                   }
               })
            }
        }
    } catch (e) {
        console.error("Failed to fetch history", e)
    }
  }

  const fetchAgents = async () => {
      try {
          const res = await fetch('/api/agents')
          if (res.ok) {
              setAgents(await res.json())
          }
      } catch (e) {
          console.error("Failed to fetch agents", e)
      }
  }

  const handleDeleteHistory = async (e: React.MouseEvent, runId: string) => {
      e.stopPropagation() // Prevent selecting the item
      if (!confirm("Are you sure you want to delete this mission?")) return

      try {
          const res = await fetch(`/api/history/${runId}`, { method: 'DELETE' })
          if (res.ok) {
              setHistory(prev => prev.filter(item => item.run_id !== runId))
              // If we deleted the currently selected run, deselect it
              if (selectedRun?.run_id === runId) {
                  setSelectedRun(null)
                  setResult(null)
              }
          }
      } catch (err) {
          console.error("Failed to delete", err)
      }
  }

  const handleStart = async (customPrompt?: string) => {
    const textToRun = customPrompt || prompt
    if (!textToRun.trim()) return
    
    // Update prompt state if it was a rerun
    if (customPrompt) setPrompt(customPrompt)
    
    setIsLoading(true)
    setError(null)
    setResult(null)
    setSelectedRun(null)
    setFormInputs({}) 
    setIsDrawerOpen(false) // Close drawer on start
    setShowSwarm(false)

    try {
      const response = await fetch('/api/run/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_description: textToRun }),
      })

      // SAFE PARSING: Handle non-JSON errors
      const text = await response.text()
      let data
      try {
          data = JSON.parse(text)
      } catch (e) {
          throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}...`)
      }
      
      if (!response.ok) throw new Error(data.detail || 'Failed to start run')

      setResult(data)
      if (data.state !== "AWAITING_USER") {
          setSelectedRun(data)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRerun = () => {
      if (selectedRun && selectedRun.problem_description) {
          handleStart(selectedRun.problem_description)
      }
  }

  const handleContinue = async () => {
    if (!result) return
    
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/run/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            run_id: result.run_id,
            problem_description: prompt,
            inputs: formInputs 
        }),
      })

      // SAFE PARSING
      const text = await response.text()
      let data
      try {
          data = JSON.parse(text)
      } catch (e) {
          throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}...`)
      }
      
      if (!response.ok) throw new Error(data.detail || 'Failed to continue run')

      setResult(data)
      setSelectedRun(data) 
      
      if (data.state === "COMPLETED") {
          fetchHistory(false) 
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (name: string, value: string) => {
    setFormInputs(prev => ({
        ...prev,
        [name]: value
    }))
  }
  
  const selectHistoryItem = (item: any) => {
      setSelectedRun({
           run_id: item.run_id,
           state: "COMPLETED",
           problem_description: item.problem_description, 
           summary: "Loaded from history",
           payload: {
               trace_log: item.metadata?.trace_log || [],
               code_url: `https://github.com/beam-me/user-code/blob/main/${item.file_path}`,
               execution_result: { stdout: "Run execution to see live output." }
           }
      })
      setIsDrawerOpen(false) 
      setShowSwarm(false)
  }

  const handleNewMission = () => {
      setSelectedRun(null)
      setResult(null)
      setPrompt("")
      setIsDrawerOpen(false)
      setShowSwarm(false)
  }

  const toggleSwarm = () => {
      setShowSwarm(!showSwarm)
      setIsDrawerOpen(false)
  }

  // --- SWARM VISUALIZATION COMPONENTS ---
  const AgentNode = ({ agent }: { agent: AgentProfile }) => {
      const isSelected = selectedAgent?.id === agent.id;
      return (
          <button 
             onClick={() => setSelectedAgent(agent)}
             className={`relative group flex flex-col items-center gap-3 p-4 rounded-2xl border transition-all duration-300 ${isSelected ? 'bg-beam-900/40 border-beam-500 scale-105 shadow-xl shadow-beam-500/20' : 'bg-slate-900/50 border-slate-800 hover:border-slate-600 hover:bg-slate-800/50'}`}
          >
              <div className="w-16 h-16 rounded-full bg-slate-950 border-2 border-slate-700 flex items-center justify-center text-3xl shadow-inner group-hover:border-beam-500/50 transition-colors relative">
                  {agent.icon}
                  {/* Status Dot */}
                  <span className="absolute top-0 right-0 w-4 h-4 bg-green-500 border-2 border-slate-950 rounded-full animate-pulse"></span>
              </div>
              <div className="text-center">
                  <div className="font-bold text-white group-hover:text-beam-300 transition-colors">{agent.name}</div>
                  <div className="text-xs text-slate-500 font-mono uppercase tracking-wider">{agent.role}</div>
              </div>
          </button>
      )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden flex flex-col">
      
      {/* PERSISTENT HEADER */}
      <div className="h-16 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-950/80 backdrop-blur z-50 relative">
          <div className="flex items-center gap-4">
              <button 
                  onClick={() => setIsDrawerOpen(!isDrawerOpen)}
                  className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                  title="Toggle Mission Log"
              >
                  {isDrawerOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              
              <h1 className="text-xl font-bold bg-gradient-to-r from-beam-500 to-indigo-500 bg-clip-text text-transparent hidden sm:block">
                  Beam.me <span className="text-slate-600 font-mono text-sm ml-2">v2.0</span>
              </h1>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
              {isLoading && <span className="text-beam-400 text-sm animate-pulse flex items-center gap-2 mr-4"><Loader2 className="w-3 h-3 animate-spin" /> Swarm Active</span>}
              
              <button 
                  onClick={toggleSwarm}
                  className={`p-2 rounded-lg transition-all ${showSwarm ? 'bg-beam-500/20 text-beam-300' : 'hover:bg-slate-800 text-slate-400'}`}
                  title="Swarm Intelligence"
              >
                  <Network className="w-5 h-5" />
              </button>

              <div className="h-6 w-px bg-slate-800 hidden sm:block"></div>

              <button 
                  onClick={handleNewMission}
                  className="bg-beam-600 hover:bg-beam-500 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 shadow-lg shadow-beam-900/20 transition-all hover:scale-105"
              >
                  <Sparkles className="w-4 h-4" />
                  <span className="hidden sm:inline">New Mission</span>
              </button>
          </div>
      </div>

      {/* DRAWER LAYOUT */}
      <div className="flex-1 relative overflow-hidden flex">
          
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
                        onClick={() => selectHistoryItem(item)}
                        className={`w-full text-left p-3 rounded text-xs transition-colors border group cursor-pointer relative ${selectedRun?.run_id === item.run_id ? 'bg-beam-900/20 border-beam-600 text-white' : 'hover:bg-slate-800 border-transparent text-slate-400'}`}
                      >
                          <div className="font-medium truncate group-hover:text-beam-300 transition-colors pr-6">{item.problem_description}</div>
                          <div className="mt-1 flex items-center justify-between opacity-50">
                              <span>{new Date(item.created_at).toLocaleDateString()}</span>
                              <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </div>
                          <button
                              onClick={(e) => handleDeleteHistory(e, item.run_id)}
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

          {/* === SWARM INTEL VIEW === */}
          {showSwarm ? (
              <div className="flex-1 overflow-y-auto w-full bg-slate-950 animate-in fade-in zoom-in-95 duration-300 flex">
                  {/* Left: Agent Grid */}
                  <div className="flex-1 p-8 overflow-y-auto">
                      <div className="max-w-4xl mx-auto">
                          <div className="text-center mb-12">
                               <h2 className="text-3xl font-extrabold text-white mb-2 flex items-center justify-center gap-3">
                                   <Cpu className="w-8 h-8 text-beam-500" />
                                   Neural Grid
                               </h2>
                               <p className="text-slate-400">Real-time status of the active agent swarm.</p>
                          </div>
                          
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                              {agents.map(agent => <AgentNode key={agent.id} agent={agent} />)}
                          </div>
                      </div>
                  </div>

                  {/* Right: Agent Dossier (Inspector) */}
                  <div className={`w-96 border-l border-slate-800 bg-slate-900/50 backdrop-blur p-6 overflow-y-auto transition-all duration-300 ${selectedAgent ? 'translate-x-0' : 'translate-x-full hidden lg:block'}`}>
                      {selectedAgent ? (
                          <div className="space-y-8 animate-in slide-in-from-right">
                              <div className="text-center">
                                  <div className="text-6xl mb-4">{selectedAgent.icon}</div>
                                  <h3 className="text-2xl font-bold text-white">{selectedAgent.name}</h3>
                                  <div className="text-beam-400 font-mono text-sm mt-1">{selectedAgent.role}</div>
                              </div>
                              
                              <div className="space-y-4">
                                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-slate-300 text-sm leading-relaxed">
                                      {selectedAgent.description}
                                  </div>
                              </div>

                              <div className="space-y-3">
                                  <h4 className="font-bold text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                                      <ShieldCheck className="w-4 h-4 text-green-400" /> Prime Directives
                                  </h4>
                                  <ul className="space-y-2">
                                      {selectedAgent.instructions.map((inst, i) => (
                                          <li key={i} className="flex gap-3 text-sm text-slate-400">
                                              <span className="text-beam-500">•</span>
                                              {inst}
                                          </li>
                                      ))}
                                  </ul>
                              </div>

                              <div className="space-y-3">
                                  <h4 className="font-bold text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                                      <Zap className="w-4 h-4 text-yellow-400" /> Tools & Capabilities
                                  </h4>
                                  <div className="flex flex-wrap gap-2">
                                      {selectedAgent.tools.map(tool => (
                                          <span key={tool} className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-300 border border-slate-700">
                                              {tool}
                                          </span>
                                      ))}
                                  </div>
                              </div>

                              <div className="space-y-3 pt-6 border-t border-slate-800">
                                  <h4 className="font-bold text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                                      <Share2 className="w-4 h-4 text-blue-400" /> Communication
                                  </h4>
                                  <div className="grid grid-cols-2 gap-4 text-xs">
                                      <div>
                                          <div className="text-slate-500 mb-2">Receives From</div>
                                          {selectedAgent.relationships.incoming.map(a => (
                                              <div key={a} className="flex items-center gap-2 text-slate-300 mb-1">
                                                  <ArrowRight className="w-3 h-3 text-slate-600 rotate-180" /> {a}
                                              </div>
                                          ))}
                                      </div>
                                      <div>
                                          <div className="text-slate-500 mb-2">Sends To</div>
                                          {selectedAgent.relationships.outgoing.map(a => (
                                              <div key={a} className="flex items-center gap-2 text-slate-300 mb-1">
                                                  <ArrowRight className="w-3 h-3 text-slate-600" /> {a}
                                              </div>
                                          ))}
                                      </div>
                                  </div>
                              </div>
                          </div>
                      ) : (
                          <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center px-8">
                              <Cpu className="w-16 h-16 mb-4 opacity-20" />
                              <p>Select an agent node to view its classified dossier.</p>
                          </div>
                      )}
                  </div>
              </div>
          ) : (
          
          /* === MAIN CONTENT AREA (Existing View) === */
          <div className="flex-1 overflow-y-auto p-4 sm:p-8 pb-32 w-full max-w-5xl mx-auto">
              
              {/* 1. INPUT AREA (Only if no active run) */}
              {!selectedRun && (
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
                          onClick={() => handleStart()}
                          disabled={!prompt.trim() || isLoading}
                          className="absolute bottom-4 right-4 bg-beam-600 hover:bg-beam-500 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-bold shadow-lg flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
                        >
                           {isLoading ? <Loader2 className="animate-spin" /> : <ArrowRight />}
                           Initialize
                        </button>
                      </div>
                      {error && <div className="text-red-400 text-center bg-red-900/20 p-2 rounded border border-red-900/50">{error}</div>}
                  </div>
              )}

              {/* 2. FORM INTERFACE (If Awaiting User) */}
              {result && result.state === "AWAITING_USER" && !selectedRun && (
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
                                        onChange={(e) => handleInputChange(variable.name, e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleContinue()}
                                    />
                                </div>
                            ))}
                        </div>

                        {error && <div className="text-red-400 mt-4 text-sm bg-red-900/20 p-2 rounded">{error}</div>}

                        <div className="flex justify-end gap-3 mt-8">
                            <button 
                                onClick={handleContinue}
                                disabled={isLoading}
                                className="bg-beam-600 hover:bg-beam-500 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 shadow-lg hover:shadow-beam-900/40 transition-all transform hover:-translate-y-0.5"
                            >
                                {isLoading ? <Loader2 className="animate-spin" /> : <Play className="w-4 h-4" />}
                                Execute Simulation
                            </button>
                        </div>
                  </div>
              )}

              {/* 3. MIND OF THE AGENT STREAM */}
              {selectedRun && (
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
                              {/* RERUN BUTTON */}
                              {selectedRun.problem_description && (
                                  <button 
                                      onClick={handleRerun}
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

                      {/* OUTPUT TERMINAL */}
                      {selectedRun.payload?.execution_result && (
                          <div className="bg-black rounded-xl border border-slate-800 overflow-hidden font-mono text-sm shadow-2xl ring-1 ring-white/5">
                              <div className="bg-slate-900/50 px-4 py-2 flex items-center gap-2 border-b border-slate-800">
                                  <Terminal className="w-4 h-4 text-slate-500" />
                                  <span className="text-slate-500 font-bold uppercase tracking-wider text-xs">Output Console</span>
                              </div>
                              <div className="p-6 text-green-400 whitespace-pre-wrap leading-relaxed">
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
                      )}

                      {/* AGENT THOUGHT STREAM */}
                      <div className="relative pl-8 space-y-8 before:absolute before:left-3.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-gradient-to-b before:from-beam-500/50 before:to-slate-800/20">
                          {selectedRun.payload?.trace_log?.map((log: LogEntry, i: number) => (
                              <div key={i} className="relative animate-in fade-in slide-in-from-bottom-4 duration-500" style={{animationDelay: `${i * 100}ms`}}>
                                  {/* Icon Bubble */}
                                  <div className="absolute -left-8 top-0 w-8 h-8 bg-slate-900 border border-slate-700 rounded-full flex items-center justify-center text-lg shadow-lg z-10 ring-4 ring-slate-950">
                                      {log.icon}
                                  </div>
                                  
                                  {/* Content Card */}
                                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-beam-500/30 transition-all shadow-sm group">
                                      <div className="flex items-center justify-between mb-2">
                                          <div className="flex items-center gap-2">
                                              <span className="text-beam-400 font-bold text-xs uppercase tracking-widest">{log.agent}</span>
                                              <span className="text-slate-600 text-xs px-2 py-0.5 bg-slate-800 rounded-full">{log.step}</span>
                                          </div>
                                          <span className="text-slate-600 text-xs font-mono">{new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                                      </div>
                                      <p className="text-slate-300 text-sm leading-relaxed group-hover:text-white transition-colors">{log.content}</p>
                                  </div>
                              </div>
                          ))}
                          <div ref={streamEndRef} className="h-4" />
                      </div>

                  </div>
              )}
          </div>
          )}
      </div>
    </div>
  )
}

export default App
