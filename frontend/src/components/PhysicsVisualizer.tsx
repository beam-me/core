import { Calculator, Variable, ArrowRight, BookOpen } from 'lucide-react';

interface PhysicsData {
  analysis: {
    knowns: Record<string, string>;
    unknowns: string[];
    assumptions?: string[];
  };
  steps: string[];
  final_answer: {
    value: number;
    unit: string;
    variable: string;
  };
  reasoning?: string;
}

interface PhysicsVisualizerProps {
  data: PhysicsData;
}

export function PhysicsVisualizer({ data }: PhysicsVisualizerProps) {
  // If data is missing or malformed, return null safely
  if (!data || !data.analysis || !data.final_answer) return null;

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden shadow-2xl ring-1 ring-white/5 my-6">
      
      {/* Header */}
      <div className="bg-slate-800/50 px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-purple-400" />
            <span className="font-bold text-white text-sm tracking-wide">PHYSICS ENGINE</span>
        </div>
        <div className="px-2 py-1 bg-purple-900/30 border border-purple-500/20 rounded text-xs text-purple-300 font-mono">
            Newtonian Solver
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Left Col: Variables & Formula */}
        <div className="space-y-6">
            
            {/* Knowns */}
            <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Variable className="w-3 h-3" /> Known Variables
                </h4>
                <div className="grid grid-cols-2 gap-3">
                    {Object.entries(data.analysis.knowns).map(([key, val]) => (
                        <div key={key} className="bg-slate-950/50 border border-slate-800 p-3 rounded-lg flex justify-between items-center group hover:border-green-500/30 transition-colors">
                            <span className="font-mono text-slate-400 font-bold">{key}</span>
                            <span className="font-mono text-green-400">{val}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Unknowns */}
            <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <ArrowRight className="w-3 h-3" /> Target
                </h4>
                <div className="bg-slate-950/50 border border-slate-800 p-3 rounded-lg flex items-center gap-2 border-l-4 border-l-orange-500">
                    <span className="text-slate-400 text-sm">Find:</span>
                    <div className="flex gap-2">
                        {data.analysis.unknowns.map(v => (
                            <span key={v} className="font-mono text-orange-400 font-bold bg-orange-900/20 px-2 py-0.5 rounded border border-orange-500/20">{v}</span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Assumptions */}
            {data.analysis.assumptions && data.analysis.assumptions.length > 0 && (
                <div className="text-xs text-slate-500 font-mono italic">
                    Assumed: {data.analysis.assumptions.join(", ")}
                </div>
            )}
        </div>

        {/* Right Col: Solution & Result */}
        <div className="flex flex-col h-full">
            
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <BookOpen className="w-3 h-3" /> Solution Path
            </h4>

            {/* Steps Scroll */}
            <div className="flex-grow bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300 space-y-4 max-h-[200px] overflow-y-auto mb-6">
                {data.steps.map((step, i) => (
                    <div key={i} className="flex gap-3">
                        <span className="text-slate-600 select-none">{i+1}.</span>
                        <span>{step}</span>
                    </div>
                ))}
            </div>

            {/* Final Answer Banner */}
            <div className="mt-auto bg-gradient-to-r from-purple-900/40 to-blue-900/40 border border-purple-500/30 rounded-xl p-6 text-center shadow-lg relative overflow-hidden group">
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Result</div>
                <div className="text-4xl font-black text-white font-mono tracking-tighter">
                    {data.final_answer.value} <span className="text-2xl text-purple-300">{data.final_answer.unit}</span>
                </div>
                <div className="text-purple-400/60 text-sm font-mono mt-1">
                    {data.final_answer.variable}
                </div>
            </div>

        </div>
      </div>
    </div>
  );
}
