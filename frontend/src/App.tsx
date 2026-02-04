import { useState, useEffect } from 'react'
import { Sparkles, Loader2, Menu, X, Network } from 'lucide-react'
import { HistoryDrawer } from './components/HistoryDrawer'
import { SwarmView } from './components/SwarmView'
import { RunStream } from './components/RunStream'
import { InputArea } from './components/InputArea'
import { useMissionControl } from './hooks/useMissionControl'

function App() {
  // Use the custom hook for all mission logic
  const {
    prompt, setPrompt,
    isLoading,
    result,
    error,
    history,
    agents,
    selectedRun, setSelectedRun,
    formInputs,
    fetchHistory,
    fetchAgents,
    deleteHistory,
    startMission,
    continueMission,
    handleInputChange,
    resetMission
  } = useMissionControl()

  // View Modes & UI State
  const [showSwarm, setShowSwarm] = useState(false)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  // Initial Data Fetch
  useEffect(() => {
    fetchHistory(true)
    fetchAgents()
  }, [fetchHistory, fetchAgents])

  // UI Handlers
  const handleDeleteHistory = (e: React.MouseEvent, runId: string) => {
    e.stopPropagation()
    if (confirm("Are you sure you want to delete this mission?")) {
      deleteHistory(runId)
    }
  }

  const handleStartWrapper = (customPrompt?: string) => {
    setIsDrawerOpen(false)
    setShowSwarm(false)
    startMission(customPrompt)
  }

  const handleRerun = () => {
    if (selectedRun && selectedRun.problem_description) {
      handleStartWrapper(selectedRun.problem_description)
    }
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
    resetMission()
    setIsDrawerOpen(false)
    setShowSwarm(false)
  }

  const toggleSwarm = () => {
    setShowSwarm(!showSwarm)
    setIsDrawerOpen(false)
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
          
          <HistoryDrawer 
            isDrawerOpen={isDrawerOpen}
            setIsDrawerOpen={setIsDrawerOpen}
            history={history}
            selectedRun={selectedRun}
            onSelectHistoryItem={selectHistoryItem}
            onDeleteHistory={handleDeleteHistory}
          />

          {/* === SWARM INTEL VIEW === */}
          {showSwarm ? (
              <SwarmView agents={agents} />
          ) : (
          
          /* === MAIN CONTENT AREA === */
          <div className="flex-1 overflow-y-auto p-4 sm:p-8 pb-32 w-full max-w-5xl mx-auto">
              
              <InputArea 
                  prompt={prompt}
                  setPrompt={setPrompt}
                  isLoading={isLoading}
                  onStart={() => handleStartWrapper()}
                  result={result}
                  formInputs={formInputs}
                  onInputChange={handleInputChange}
                  onContinue={continueMission}
                  error={error}
              />

              <RunStream 
                  selectedRun={selectedRun}
                  isLoading={isLoading}
                  onRerun={handleRerun}
              />
          </div>
          )}
      </div>
    </div>
  )
}

export default App
