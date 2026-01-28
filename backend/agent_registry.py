from typing import List, Dict

AGENT_REGISTRY = [
    {
        "id": "hmao.orchestrator",
        "name": "Global Orchestrator",
        "role": "HMAO System Gateway",
        "icon": "📡",
        "description": "The central authority. Decomposes prompts into DAGs, dispatches tasks to Discipline Cores, and arbitrates conflicts. Owns the global state.",
        "instructions": [
            "Decompose User Prompt into Task DAG.",
            "Dispatch subtasks to specialized Cores.",
            "Maintain authoritative global state.",
            "Aggregate artifacts (Analysis -> Code).",
            "Pause for User Input if clarification is needed."
        ],
        "tools": ["Task DAG", "State Management", "Conflict Arbitration"],
        "relationships": {
            "incoming": ["User"],
            "outgoing": ["Analysis Core", "Engineering Core"]
        }
    },
    {
        "id": "analysis_core",
        "name": "Analysis Core",
        "role": "Discipline Core (Triad)",
        "icon": "🧐",
        "description": "Specialized core for requirement elicitation and variable extraction. Operates under strict Planner-Executor-Critic cycle.",
        "instructions": [
            "Planner: Identify missing physics variables.",
            "Executor: Use LLM to extract JSON schema.",
            "Critic: Validate variable types and completeness."
        ],
        "tools": ["Problem Framer (LLM)", "Schema Validator"],
        "relationships": {
            "incoming": ["Global Orchestrator"],
            "outgoing": ["Global Orchestrator"]
        }
    },
    {
        "id": "engineering_core",
        "name": "Engineering Core",
        "role": "Discipline Core (Triad)",
        "icon": "🛠️",
        "description": "Specialized core for implementation and verification. Encapsulates Code Writing, GitHub Ops, and Simulation Execution.",
        "instructions": [
            "Planner: Design Python solution architecture.",
            "Executor: Generate code (CodeWriter) & Push to GitHub.",
            "Executor: Run Simulation (Runner).",
            "Critic: Validate Exit Code 0 and Output format (QA)."
        ],
        "tools": ["Code Writer", "GitHub API", "Python Sandbox", "QA Validator"],
        "relationships": {
            "incoming": ["Global Orchestrator"],
            "outgoing": ["Global Orchestrator", "GitHub Repo"]
        }
    }
]
