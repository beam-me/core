import { useState } from 'react'
import { Cpu, ShieldCheck, Zap, Share2, ArrowRight } from 'lucide-react'
import { AgentProfile } from '../types'

interface SwarmViewProps {
  agents: AgentProfile[];
}

export function SwarmView({ agents }: SwarmViewProps) {
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null)

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
  )
}
