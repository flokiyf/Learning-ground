"""
LearnForge MCP — Simulation: Mise en situation métier.
Domaines : dev, devops, medicine, management, finance, sales, law.
Scénarios : incident, design, review, diagnosis, negotiation.
Inputs contextuels : code_editor, terminal, rich_text, form.
"""
import json
import uuid
from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Simulation")

# --- Tools ---

@mcp.tool(tags={"session", "setup"}, timeout=15.0)
async def create_scenario(
    domain: Annotated[str, "dev | devops | medicine | management | finance | sales | law"],
    role: Annotated[str, "Rôle à incarner (ex: senior_dev, team_lead)"],
    difficulty: Annotated[str, "junior | mid | senior | crisis"] = "mid",
    scenario_type: Annotated[str, "incident | design | review | diagnosis | negotiation"] = "incident",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Crée un scénario de mise en situation."""
    scenario_id = str(uuid.uuid4())[:8]
    title = f"Scénario {scenario_type} — {domain} ({role})"
    context = f"Vous êtes {role} dans un contexte {domain}. Difficulté : {difficulty}."
    initial = "Un incident a été signalé en production. Vous devez investiguer et proposer une solution."
    input_type = "code_editor" if domain in ("dev", "devops") else "rich_text" if scenario_type == "negotiation" else "form" if scenario_type == "diagnosis" else "rich_text"
    characters = [
        {"id": "client", "name": "Client / Product Owner", "role": "stakeholder"},
        {"id": "colleague", "name": "Collègue technique", "role": "peer"},
    ]
    await ctx.set_state("scenario_id", scenario_id)
    await ctx.set_state("domain", domain)
    await ctx.set_state("role", role)
    await ctx.set_state("situation", initial)
    await ctx.set_state("characters", characters)
    await ctx.set_state("narrative_history", [])
    await ctx.set_state("input_type", input_type)
    return ToolResult(
        content=f"Scénario créé : {title}. Contexte : {context}. Situation initiale : {initial}",
        structured_content={
            "scenario_id": scenario_id,
            "title": title,
            "context": context,
            "initial_situation": initial,
            "input_type": input_type,
            "characters": characters,
        },
    )


@mcp.tool(tags={"session", "core"})
async def advance_scenario(
    user_action: Annotated[str, "Action ou décision de l'utilisateur"],
    input_type: Annotated[str, "text | code | command"] = "text",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Fait avancer le scénario selon l'action de l'utilisateur."""
    history = await ctx.get_state("narrative_history") or []
    situation = await ctx.get_state("situation") or ""
    history.append({"user_action": user_action, "input_type": input_type})
    new_situation = situation + f" Suite à votre action : le système réagit. Prochaine étape : valider avec le client."
    await ctx.set_state("narrative_history", history)
    await ctx.set_state("situation", new_situation)
    return ToolResult(
        content=new_situation,
        structured_content={
            "narrative_response": new_situation,
            "new_situation": new_situation,
            "characters_reactions": [{"id": "client", "reaction": "D'accord, on attend la correction."}],
            "score_delta": 5,
            "critical_moment": False,
        },
    )


@mcp.tool(tags={"session", "core"})
async def inject_event(
    event_type: Annotated[str, "complication | new_info | stakeholder_pressure | system_failure"],
    severity: Annotated[str, "minor | major | critical"] = "major",
    ctx: Context = CurrentContext(),
) -> str:
    """Injecte un événement dans le scénario (complication, pression, panne)."""
    events = {"complication": "Une nouvelle régression apparaît sur un autre module.", "new_info": "Le client précise que la deadline est avancée.", "stakeholder_pressure": "La direction demande un point dans 1h.", "system_failure": "Le serveur de staging est indisponible."}
    desc = events.get(event_type, events["complication"]) + f" Sévérité : {severity}."
    history = await ctx.get_state("narrative_history") or []
    history.append({"type": "injected_event", "event_type": event_type, "severity": severity, "description": desc})
    await ctx.set_state("narrative_history", history)
    return desc


@mcp.tool(tags={"session", "core"})
async def get_system_response(
    command: Annotated[str, "Commande ou requête simulée (ex: commande shell, API)"],
    ctx: Context = CurrentContext(),
) -> str:
    """Simule la réponse du système (terminal, API) cohérente avec le scénario."""
    return f"[Simulation] Exécution de « {command[:50]} » : OK, sortie simulée (exit 0)."


@mcp.tool(tags={"session", "core"})
async def evaluate_decision(
    decision: Annotated[str, "Décision prise"],
    rationale: Annotated[str, "Justification"] = "",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Évalue une décision : conséquence, optimalité, alternatives, scores."""
    return ToolResult(
        content="Décision jugée correcte. Une alternative aurait été de déployer d'abord en staging.",
        structured_content={
            "consequence": "Déploiement validé.",
            "was_optimal": True,
            "alternative_approaches": ["Déployer en staging d'abord", "Ajouter des tests"],
            "rubric_scores": {"technical": 8, "communication": 7, "judgment": 8},
        },
    )


@mcp.tool(tags={"session", "output"})
async def end_simulation(ctx: Context = CurrentContext()) -> ToolResult:
    """Termine la simulation et retourne le bilan."""
    history = await ctx.get_state("narrative_history") or []
    domain = await ctx.get_state("domain") or "general"
    return ToolResult(
        content="Simulation terminée. Bilan : objectifs atteints à 75%.",
        structured_content={
            "final_score": 75,
            "performance_by_competency": {"technical": 80, "communication": 70, "judgment": 75},
            "key_decisions": [h.get("user_action", "")[:80] for h in history if "user_action" in h][:5],
            "missed_opportunities": ["Demander plus de contexte au client"],
            "overall_feedback": "Bonne réactivité. À améliorer : communication des risques.",
        },
    )


# --- Resources ---

@mcp.resource("simulation://scenarios/{domain}", mime_type="application/json")
def list_scenarios(domain: str) -> str:
    """Templates de scénarios disponibles par domaine."""
    templates = {
        "dev": [{"id": "incident_1", "title": "Bug production"}, {"id": "review_1", "title": "Code review"}],
        "devops": [{"id": "incident_infra", "title": "Incident infrastructure"}],
        "medicine": [{"id": "diagnosis_1", "title": "Diagnostic différentiel"}],
        "management": [{"id": "conflict_1", "title": "Conflit d'équipe"}],
    }
    return json.dumps(templates.get(domain, templates["dev"]))


@mcp.resource("simulation://scenarios/{domain}/{scenario_id}", mime_type="application/json")
def get_scenario_template(domain: str, scenario_id: str) -> str:
    """Détail d'un template de scénario."""
    return json.dumps({"domain": domain, "scenario_id": scenario_id, "title": "Scénario type", "context": "Contexte type", "steps": []})


@mcp.resource("simulation://roles/{domain}", mime_type="application/json")
def list_roles(domain: str) -> str:
    """Rôles disponibles par domaine."""
    roles = {"dev": ["junior_dev", "senior_dev", "tech_lead"], "devops": ["sre", "platform_engineer"], "management": ["team_lead", "manager"], "medicine": ["junior_doctor", "senior_doctor"]}
    return json.dumps(roles.get(domain, ["default"]))


@mcp.resource("simulation://events/{domain}", mime_type="application/json")
def list_events(domain: str) -> str:
    """Bibliothèque d'événements injectables par domaine."""
    events = ["complication", "new_info", "stakeholder_pressure", "system_failure"]
    return json.dumps({"domain": domain, "events": events})


@mcp.resource("simulation://rubrics/{domain}", mime_type="application/json")
def get_rubric(domain: str) -> str:
    """Grille d'évaluation par domaine."""
    return json.dumps({"domain": domain, "criteria": ["technical", "communication", "judgment"], "scale": "0-10"})


@mcp.resource("simulation://session/{session_id}/log", mime_type="application/json")
async def get_session_log(session_id: str, ctx: Context) -> str:
    """Journal de la session de simulation."""
    history = await ctx.get_state("narrative_history") or []
    return json.dumps({"session_id": session_id, "log": history})


# --- Prompts ---

@mcp.prompt(tags={"narrator"})
def scenario_narrator_prompt(domain: str, scenario_context: str, current_state: str) -> list[Message]:
    """Narrateur du scénario."""
    return [
        Message(
            f"Tu es le narrateur d'une simulation {domain}. Contexte : {scenario_context}. État actuel : {current_state}. Décris la suite de l'action de façon immersive.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"character-persona"})
def client_persona_prompt(scenario_type: str, pressure_level: str = "normal") -> list[Message]:
    """Persona client / stakeholder."""
    return [
        Message(
            f"Tu incarnes le client dans un scénario {scenario_type}. Niveau de pression : {pressure_level}. Réagis de façon réaliste aux décisions de l'utilisateur.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"character-persona"})
def colleague_prompt(expertise: str, attitude: str = "neutral") -> list[Message]:
    """Persona collègue (neutral | hostile | helpful)."""
    return [
        Message(
            f"Tu incarnes un collègue expert en {expertise}, attitude {attitude}. Réagis aux demandes de l'utilisateur de façon cohérente.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"evaluation"})
def debrief_prompt(domain: str, simulation_log: str, rubric: str) -> list[Message]:
    """Débriefing et évaluation de la simulation."""
    return [
        Message(
            f"Débriefing simulation {domain}. Log : {simulation_log[:600]}... Grille : {rubric}. Donne un feedback structuré : points forts, axes d'amélioration, score par critère.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"terminal"})
def terminal_simulator_prompt(os_type: str, scenario_context: str, history: list[str]) -> list[Message]:
    """Simulateur de terminal cohérent avec le scénario."""
    return [
        Message(
            f"Tu simules un terminal {os_type}. Contexte scénario : {scenario_context}. Historique des commandes : {history[-5:]}. Réponds de façon réaliste à la prochaine commande.",
            role="user",
        ),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8006)


if __name__ == "__main__":
    run()
