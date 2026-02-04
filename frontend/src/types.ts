export interface LogEntry {
    agent: string;
    step: string;
    content: string;
    icon: string;
    timestamp: string;
}

export interface AgentProfile {
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
