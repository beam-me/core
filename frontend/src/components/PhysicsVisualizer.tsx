import { Calculator, Variable, ArrowRight, BookOpen, BarChart3 } from 'lucide-react';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

interface PhysicsData {
  analysis: {
    knowns: Record<string, any>;
    unknowns: string[];
    assumptions?: string[];
  };
  steps: string[];
  final_answer: {
    value: any; 
    unit: string;
    variable: string;
  };
  reasoning?: string;
}

interface PhysicsVisualizerProps {
  data: PhysicsData;
}

// --- Physics Constants (Mirrors PAVPhysics) ---
const RHO_STD = 0.002378;
const MPH_TO_FTS = 1.46667;

export function PhysicsVisualizer({ data }: PhysicsVisualizerProps) {
  if (!data || !data.analysis || !data.final_answer) {
      return null;
  }

  const renderValue = (val: any): string => {
      if (typeof val === 'object' && val !== null) {
          if (val.value !== undefined && val.unit !== undefined) return `${val.value}`;
          if (val.value !== undefined) return String(val.value);
          return JSON.stringify(val);
      }
      return String(val);
  };

  const renderUnit = (val: any): string => {
       if (typeof val === 'object' && val !== null && val.unit) return val.unit;
       return '';
  }

  // --- CHART GENERATION LOGIC ---
  // Try to extract key parameters for generating a drag/power curve
  const area = parseFloat(String(data.analysis.knowns["Propeller Disc Area"] || data.analysis.knowns["area"] || "8").replace(/[^0-9.]/g, ''));
  // Default drag coeff if not found (0.05 for a streamlined drone, 1.0 for a brick)
  const cd = 0.5; 
  
  // Generate data points (0 to 80 mph)
  const chartData = [];
  for (let mph = 0; mph <= 80; mph += 5) {
      const v_fts = mph * MPH_TO_FTS;
      
      // Dynamic Pressure (q) = 0.5 * rho * v^2
      const q = 0.5 * RHO_STD * Math.pow(v_fts, 2);
      
      // Drag Estimate (Simplified: D = q * Cd * Area)
      // Note: This is a rough approximation for visualization purposes
      const drag = q * cd * (area * 0.2); // Assume frontal area is fraction of disc area
      
      chartData.push({
          speed: mph,
          q: parseFloat(q.toFixed(2)),
          drag: parseFloat(drag.toFixed(2)),
      });
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden shadow-2xl ring-1 ring-white/5 my-6 animate-in fade-in slide-in-from-bottom-4">
      
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
                    {data.analysis.knowns && Object.entries(data.analysis.knowns).map(([key, val]) => (
                        <div key={key} className="bg-slate-950/50 border border-slate-800 p-3 rounded-lg flex justify-between items-center group hover:border-green-500/30 transition-colors">
                            <span className="font-mono text-slate-400 font-bold text-xs truncate mr-2" title={key}>{key}</span>
                            <span className="font-mono text-green-400 text-sm truncate" title={String(val)}>
                                {renderValue(val)} {renderUnit(val)}
                            </span>
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
                    <div className="flex gap-2 flex-wrap">
                        {data.analysis.unknowns && data.analysis.unknowns.map((v, idx) => (
                            <span key={`${v}-${idx}`} className="font-mono text-orange-400 font-bold bg-orange-900/20 px-2 py-0.5 rounded border border-orange-500/20 text-xs">{v}</span>
                        ))}
                    </div>
                </div>
            </div>
            
            {/* Live Chart: Dynamic Pressure vs Speed */}
            <div className="mt-6 border border-slate-800 rounded-lg bg-slate-950/50 p-4">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <BarChart3 className="w-3 h-3" /> Performance Sweep
                </h4>
                <div className="h-[180px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                            <XAxis 
                                dataKey="speed" 
                                stroke="#64748b" 
                                fontSize={10} 
                                tickLine={false}
                                label={{ value: 'Speed (mph)', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 10 }}
                            />
                            <YAxis 
                                stroke="#64748b" 
                                fontSize={10} 
                                tickLine={false}
                                label={{ value: 'q (psf)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10 }}
                            />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                                itemStyle={{ color: '#e2e8f0' }}
                                labelStyle={{ color: '#94a3b8' }}
                            />
                            <Line 
                                type="monotone" 
                                dataKey="q" 
                                stroke="#8b5cf6" 
                                strokeWidth={2} 
                                dot={false} 
                                name="Dynamic Pressure"
                            />
                            <Line 
                                type="monotone" 
                                dataKey="drag" 
                                stroke="#10b981" 
                                strokeWidth={2} 
                                dot={false} 
                                name="Drag (Est)"
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                <div className="text-[10px] text-slate-600 mt-2 text-center font-mono">
                    Simulation based on RHO_STD={RHO_STD} slugs/ft³
                </div>
            </div>

        </div>

        {/* Right Col: Solution & Result */}
        <div className="flex flex-col h-full">
            
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <BookOpen className="w-3 h-3" /> Solution Path
            </h4>

            {/* Steps Scroll */}
            <div className="flex-grow bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm text-slate-300 space-y-4 max-h-[300px] overflow-y-auto mb-6 custom-scrollbar">
                {data.steps && data.steps.map((step, i) => (
                    <div key={i} className="flex gap-3 items-start group">
                        <span className="text-slate-700 select-none font-bold text-xs mt-0.5 group-hover:text-slate-500 transition-colors">{String(i+1).padStart(2, '0')}.</span>
                        <span className="leading-relaxed">{step}</span>
                    </div>
                ))}
            </div>

            {/* Final Answer Banner */}
            <div className="mt-auto bg-gradient-to-r from-purple-950/50 to-blue-950/50 border border-purple-500/30 rounded-xl p-6 text-center shadow-lg relative overflow-hidden group">
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative z-10">
                    <div className="text-purple-400/80 text-xs font-bold uppercase tracking-widest mb-2 border-b border-purple-500/20 pb-2 inline-block px-4">Result</div>
                    <div className="text-4xl font-black text-white font-mono tracking-tighter drop-shadow-lg flex justify-center items-baseline gap-2 flex-wrap">
                        <span>{renderValue(data.final_answer.value)}</span>
                        {(data.final_answer.unit || renderUnit(data.final_answer.value)) && (
                             <span className="text-xl text-purple-300 font-bold">
                                 {data.final_answer.unit || renderUnit(data.final_answer.value)}
                             </span>
                        )}
                    </div>
                    <div className="text-purple-400/60 text-sm font-mono mt-2 bg-purple-900/20 inline-block px-3 py-1 rounded-full border border-purple-500/10">
                        {data.final_answer.variable}
                    </div>
                </div>
            </div>

        </div>
      </div>
    </div>
  );
}
