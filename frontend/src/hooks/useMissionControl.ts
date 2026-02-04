import { useState, useCallback } from 'react';
import { AgentProfile } from '../types';

interface MissionState {
  prompt: string;
  isLoading: boolean;
  result: any;
  error: string | null;
  history: any[];
  agents: AgentProfile[];
  selectedRun: any;
  formInputs: Record<string, any>;
}

export function useMissionControl() {
  const [state, setState] = useState<MissionState>({
    prompt: '',
    isLoading: false,
    result: null,
    error: null,
    history: [],
    agents: [],
    selectedRun: null,
    formInputs: {},
  });

  const setPartialState = (updates: Partial<MissionState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  const fetchHistory = useCallback(async (autoSelect = false) => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setPartialState({ history: data });

        if (autoSelect && !state.selectedRun && data.length > 0) {
          const recent = data[0];
          setPartialState({
            selectedRun: {
              run_id: recent.run_id,
              state: "COMPLETED",
              problem_description: recent.problem_description,
              summary: "Loaded from history",
              payload: {
                trace_log: recent.metadata?.trace_log || [],
                code_url: recent.metadata?.url ? `https://github.com/beam-me/user-code/blob/main/${recent.file_path}` : null,
                execution_result: { stdout: "Run execution to see live output." }
              }
            }
          });
        }
      }
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  }, [state.selectedRun]);

  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch('/api/agents');
      if (res.ok) {
        setPartialState({ agents: await res.json() });
      }
    } catch (e) {
      console.error("Failed to fetch agents", e);
    }
  }, []);

  const deleteHistory = useCallback(async (runId: string) => {
    try {
      const res = await fetch(`/api/history/${runId}`, { method: 'DELETE' });
      if (res.ok) {
        setState(prev => {
          const newHistory = prev.history.filter(item => item.run_id !== runId);
          const updates: Partial<MissionState> = { history: newHistory };
          if (prev.selectedRun?.run_id === runId) {
            updates.selectedRun = null;
            updates.result = null;
          }
          return { ...prev, ...updates };
        });
      }
    } catch (err) {
      console.error("Failed to delete", err);
    }
  }, []);

  const startMission = async (customPrompt?: string) => {
    const textToRun = customPrompt || state.prompt;
    if (!textToRun.trim()) return;

    setPartialState({
      prompt: customPrompt || state.prompt,
      isLoading: true,
      error: null,
      result: null,
      selectedRun: null,
      formInputs: {}
    });

    try {
      const response = await fetch('/api/run/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_description: textToRun }),
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}...`);
      }

      if (!response.ok) throw new Error(data.detail || 'Failed to start run');

      setPartialState({
        result: data,
        selectedRun: data.state !== "AWAITING_USER" ? data : null,
        isLoading: false
      });
    } catch (err: any) {
      setPartialState({ error: err.message, isLoading: false });
    }
  };

  const continueMission = async () => {
    if (!state.result) return;

    setPartialState({ isLoading: true, error: null });

    try {
      const response = await fetch('/api/run/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: state.result.run_id,
          problem_description: state.prompt,
          inputs: state.formInputs
        }),
      });

      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}...`);
      }

      if (!response.ok) throw new Error(data.detail || 'Failed to continue run');

      setPartialState({
        result: data,
        selectedRun: data,
        isLoading: false
      });

      if (data.state === "COMPLETED") {
        fetchHistory(false);
      }
    } catch (err: any) {
      setPartialState({ error: err.message, isLoading: false });
    }
  };

  const handleInputChange = (name: string, value: string) => {
    setState(prev => ({
      ...prev,
      formInputs: { ...prev.formInputs, [name]: value }
    }));
  };

  return {
    ...state,
    setPrompt: (p: string) => setPartialState({ prompt: p }),
    setSelectedRun: (run: any) => setPartialState({ selectedRun: run }),
    setResult: (r: any) => setPartialState({ result: r }),
    fetchHistory,
    fetchAgents,
    deleteHistory,
    startMission,
    continueMission,
    handleInputChange,
    resetMission: () => setPartialState({ selectedRun: null, result: null, prompt: "" })
  };
}
