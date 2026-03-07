"""
LearnForge MCP — Socratic: Méthode socratique pure.
Jamais de réponse directe ; uniquement des questions pour guider la découverte.
Règle exposée via resource socratic://rules.
"""
import json
import hashlib
import uuid
from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Socratic")

# --- Tools ---

@mcp.tool(tags={"session", "setup"})
async def start_socratic_session(
    topic: Annotated[str, "Sujet à explorer"],
    user_initial_belief: Annotated[str, "Ce que l'utilisateur pense déjà savoir"] = "",
    objective: Annotated[str, "discover | clarify | challenge | explore"] = "discover",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Démarre une session socratique : première question et arbre de raisonnement."""
    session_id = str(uuid.uuid4())[:8]
    entry_question = f"Qu'est-ce qui te semble le plus central dans « {topic} » ?" if not user_initial_belief else f"Tu dis que {user_initial_belief[:100]}. Comment en es-tu venu à cette idée ?"
    await ctx.set_state("topic", topic)
    await ctx.set_state("objective", objective)
    await ctx.set_state("session_id", session_id)
    await ctx.set_state("reasoning_tree", {"nodes": [{"id": "root", "concept": topic, "questions": []}], "current": "root"})
    await ctx.set_state("user_responses", [])
    await ctx.set_state("questions_asked", [entry_question])
    await ctx.set_state("concepts_discovered", [])
    await ctx.set_state("misconceptions_found", [])
    return ToolResult(
        content=f"Session socratique démarrée. Première question : {entry_question}",
        structured_content={"session_id": session_id, "entry_question": entry_question, "reasoning_tree_depth": 0},
    )


@mcp.tool(tags={"session", "core"})
async def get_next_question(
    user_response: Annotated[str, "Réponse de l'utilisateur à la question précédente"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Génère la prochaine question socratique selon la réponse (jamais de réponse directe)."""
    user_responses = await ctx.get_state("user_responses") or []
    user_responses.append(user_response)
    await ctx.set_state("user_responses", user_responses)
    questions_asked = await ctx.get_state("questions_asked") or []
    question_type = ["clarification", "implication", "assumption", "evidence", "perspective"][len(questions_asked) % 5]
    next_q = f"Si on pousse cette idée plus loin, que se passe-t-il quand on considère un contre-exemple ?"
    questions_asked.append(next_q)
    await ctx.set_state("questions_asked", questions_asked)
    progress = min(100, 10 + len(questions_asked) * 15)
    return ToolResult(
        content=next_q,
        structured_content={
            "question": next_q,
            "question_type": question_type,
            "reasoning_progress": progress,
            "is_getting_closer": progress > 30,
        },
    )


@mcp.tool(tags={"session", "navigation"})
async def track_reasoning_progress(ctx: Context = CurrentContext()) -> ToolResult:
    """Position actuelle dans l'arbre de raisonnement et chemin restant."""
    tree = await ctx.get_state("reasoning_tree") or {"nodes": [], "current": "root"}
    questions = await ctx.get_state("questions_asked") or []
    path_taken = questions[:]
    return ToolResult(
        content=f"Étapes : {len(path_taken)} questions posées. Chemin suivi : voir structured_content.",
        structured_content={
            "current_step": len(path_taken),
            "total_steps": 10,
            "concepts_touched": await ctx.get_state("concepts_discovered") or [],
            "path_taken": path_taken,
            "remaining_path": ["Approfondir implications", "Tester limites", "Synthétiser"],
        },
    )


@mcp.tool(tags={"session", "support"})
async def get_hint(
    reasoning_step: Annotated[str, "Étape ou concept sur lequel un indice est demandé"],
    ctx: Context = CurrentContext(),
) -> str:
    """Donne un indice minimal qui ne révèle pas la réponse."""
    return f"Indice pour « {reasoning_step[:50]} » : réfléchis à ce qui doit être vrai pour que ton affirmation tienne."


@mcp.tool(tags={"session", "output"})
async def analyze_understanding(ctx: Context = CurrentContext()) -> ToolResult:
    """Analyse ce qui a été découvert et les éventuelles confusions restantes."""
    discovered = await ctx.get_state("concepts_discovered") or []
    misconceptions = await ctx.get_state("misconceptions_found") or []
    responses = await ctx.get_state("user_responses") or []
    discovery_score = min(100, 20 + len(discovered) * 15 + len(responses) * 5)
    return ToolResult(
        content=f"Score de découverte : {discovery_score}/100. Concepts découverts : {discovered}. Confusions résolues : {misconceptions}.",
        structured_content={
            "discovery_score": discovery_score,
            "concepts_discovered": discovered,
            "misconceptions_resolved": misconceptions,
            "remaining_confusions": [] if discovery_score >= 70 else ["À préciser avec une question de clarification"],
        },
    )


# --- Resources ---

@mcp.resource("socratic://rules", mime_type="text/plain")
def get_socratic_rules() -> str:
    """Règle fondamentale : ne jamais donner de réponse directe ; guider uniquement par des questions."""
    return "RÈGLE SOCRATIQUE : Ne jamais donner de réponse directe. Guider l'apprenant uniquement par des questions (clarification, implication, hypothèse, preuve, perspective). La découverte doit venir de l'apprenant."


@mcp.resource("socratic://reasoning-trees/{topic_hash}", mime_type="application/json")
def get_reasoning_tree(topic_hash: str) -> str:
    """Arbre de raisonnement pré-construit pour un sujet (hash du topic)."""
    return json.dumps({
        "topic_hash": topic_hash,
        "nodes": [{"id": "root", "concept": "root", "questions_to_reach": [], "children": ["n1", "n2"]}, {"id": "n1", "concept": "definition", "questions_to_reach": ["Qu'est-ce que X ?"], "children": []}],
    })


@mcp.resource("socratic://question-types", mime_type="application/json")
def get_question_types() -> str:
    """Types de questions socratiques avec exemples."""
    data = [
        {"type": "clarification", "example": "Que veux-tu dire par... ?"},
        {"type": "implication", "example": "Si c'est vrai, que implique cela pour... ?"},
        {"type": "assumption", "example": "Sur quelle hypothèse t'appuies-tu ?"},
        {"type": "evidence", "example": "Qu'est-ce qui te fait penser que... ?"},
        {"type": "perspective", "example": "Comment quelqu'un qui défend l'avis inverse argumenterait-il ?"},
    ]
    return json.dumps(data)


@mcp.resource("socratic://session/{session_id}/path", mime_type="application/json")
async def get_session_path(session_id: str, ctx: Context) -> str:
    """Chemin parcouru dans l'arbre de raisonnement pour cette session."""
    questions = await ctx.get_state("questions_asked") or []
    responses = await ctx.get_state("user_responses") or []
    return json.dumps({"session_id": session_id, "questions_asked": questions, "user_responses": responses})


# --- Prompts ---

@mcp.prompt(tags={"system", "core"})
def pure_socratic_prompt(topic: str, reasoning_stage: int, user_responses: list[str], tree_position: str) -> list[Message]:
    """Prompt strict : ne jamais répondre directement."""
    return [
        Message(
            f"Tu appliques la méthode socratique sur « {topic} ». Étape {reasoning_stage}. Réponses de l'utilisateur : {user_responses[-3:] if user_responses else []}. Position : {tree_position}. NE DONNE JAMAIS de réponse directe. Pose UNIQUEMENT une question pour faire avancer la réflexion.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"support"})
def gentle_probe_prompt(concept: str, detected_misconception: str) -> list[Message]:
    """Question douce pour faire émerger une misconception."""
    return [Message(f"Concept : {concept}. Misconception détectée : {detected_misconception}. Pose une question gentille pour faire reformuler sans donner la réponse.", role="user")]


@mcp.prompt(tags={"support"})
def discovery_guide_prompt(topic: str, user_current_position: str, target_insight: str) -> list[Message]:
    """Guide vers une découverte cible."""
    return [
        Message(
            f"Sujet : {topic}. L'utilisateur en est à : {user_current_position}. Insight visé : {target_insight}. Pose une question qui le rapproche de cet insight sans le révéler.",
            role="user",
        ),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8005)


if __name__ == "__main__":
    run()
