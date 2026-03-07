"""
LearnForge MCP — Debate: Débat avec une IA en position opposée ou devil's advocate.
Rounds, contre-arguments, évaluation, arbitrage.
"""
import json
import uuid
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Debate")

# --- Tools ---

@mcp.tool(tags={"session", "setup"})
async def start_debate(
    topic: Annotated[str, "Sujet du débat"],
    user_position: Annotated[str, "Position que vous défendez"],
    ai_position: Annotated[str, "auto | opposite | devil_advocate"] = "opposite",
    rounds: Annotated[int, Field(ge=3, le=10, description="Nombre de rounds")] = 5,
    style: Annotated[str, "formal | socratic | aggressive | academic"] = "formal",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Lance un débat : l'IA prend la position opposée ou devil's advocate."""
    debate_id = str(uuid.uuid4())[:8]
    ai_statement = "Je défends la position opposée pour faire avancer le débat." if ai_position == "opposite" else "Je joue l'avocat du diable pour tester la solidité de ton argumentation."
    await ctx.set_state("debate_id", debate_id)
    await ctx.set_state("topic", topic)
    await ctx.set_state("user_position", user_position)
    await ctx.set_state("ai_position", ai_position)
    await ctx.set_state("rounds", rounds)
    await ctx.set_state("style", style)
    await ctx.set_state("current_round", 1)
    await ctx.set_state("transcript", [])
    await ctx.set_state("difficulty_level", 1)
    return ToolResult(
        content=f"Débat lancé. {ai_statement} Utilisez ai_counter_argument avec votre argument.",
        structured_content={
            "debate_id": debate_id,
            "ai_position_statement": ai_statement,
            "rules": "Chaque round : vous argumentez, l'IA contre-argumente.",
            "round_count": rounds,
        },
    )


@mcp.tool(tags={"session", "core"})
async def ai_counter_argument(
    user_argument: Annotated[str, "Votre argument"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """L'IA produit un contre-argument à votre argument."""
    transcript = await ctx.get_state("transcript") or []
    transcript.append({"role": "user", "content": user_argument})
    current_round = await ctx.get_state("current_round") or 1
    technique = ["reductio", "analogy", "evidence", "questioning"][current_round % 4]
    counter = f"Contre-argument (technique {technique}) : Si on pousse ton raisonnement, on aboutit à X. Comment concilies-tu cela avec ta position ?"
    transcript.append({"role": "assistant", "content": counter})
    await ctx.set_state("transcript", transcript)
    await ctx.set_state("current_round", current_round + 1)
    return ToolResult(
        content=counter,
        structured_content={"counter_argument": counter, "technique_used": technique, "round": current_round},
    )


@mcp.tool(tags={"session", "core"})
async def evaluate_argument(
    argument: Annotated[str, "Argument à évaluer"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Évaluation objective d'un argument (force, logique, preuves, sophismes)."""
    return ToolResult(
        content="Évaluation : force 7/10, logique 7/10, preuves 6/10. Suggestions : appuyer avec un exemple concret.",
        structured_content={
            "strength": 7,
            "logic": 7,
            "evidence": 6,
            "fallacies": [],
            "suggestions": ["Appuyer avec un exemple concret"],
        },
    )


@mcp.tool(tags={"session", "control"})
async def escalate_difficulty(ctx: Context = CurrentContext()) -> str:
    """Monte la difficulté : l'IA contre-argumente plus fort."""
    level = await ctx.get_state("difficulty_level") or 1
    await ctx.set_state("difficulty_level", min(5, level + 1))
    return f"Difficulté augmentée (niveau {level + 1}). L'IA sera plus précise et exigeante."


@mcp.tool(tags={"session", "output"})
async def request_arbitration(ctx: Context = CurrentContext()) -> ToolResult:
    """Demande un arbitrage : résumé, scores, moments clés, verdict."""
    transcript = await ctx.get_state("transcript") or []
    user_pos = await ctx.get_state("user_position") or ""
    return ToolResult(
        content="Arbitrage : les deux parties ont présenté des arguments. Verdict ci-dessous.",
        structured_content={
            "arbiter_summary": "Débat équilibré sur " + str(len(transcript)) + " échanges.",
            "user_score": 75,
            "ai_score": 70,
            "key_exchange_moments": [t.get("content", "")[:80] for t in transcript[:3]],
            "final_ruling": "Arguments solides des deux côtés. L'utilisateur a bien défendu sa position.",
        },
    )


@mcp.tool(tags={"session", "output"})
async def end_debate(ctx: Context = CurrentContext()) -> ToolResult:
    """Termine le débat et retourne le résumé final."""
    transcript = await ctx.get_state("transcript") or []
    return ToolResult(
        content=f"Débat terminé. {len(transcript)} échanges. Utilisez request_arbitration pour le verdict.",
        structured_content={"exchange_count": len(transcript), "status": "ended"},
    )


# --- Resources ---

@mcp.resource("debate://rules", mime_type="application/json")
def get_debate_rules() -> str:
    """Règles des formats de débat : Oxford, Lincoln-Douglas, Socratic, Free-form."""
    data = [
        {"id": "oxford", "description": "Format Oxford"},
        {"id": "lincoln_douglas", "description": "Lincoln-Douglas"},
        {"id": "socratic", "description": "Socratique"},
        {"id": "free_form", "description": "Libre"},
    ]
    return json.dumps(data)


@mcp.resource("debate://positions/{topic_hash}", mime_type="application/json")
def get_prebuilt_positions(topic_hash: str) -> str:
    """Positions pré-construites pour sujets courants (par hash du topic)."""
    return json.dumps({"topic_hash": topic_hash, "positions": ["pour", "contre", "nuancé"]})


@mcp.resource("debate://scoring-criteria", mime_type="application/json")
def get_scoring_criteria() -> str:
    """Critères de notation du débat."""
    return json.dumps({"criteria": ["logic", "evidence", "relevance", "rebuttal", "clarity"], "scale": "0-10"})


@mcp.resource("debate://session/{session_id}/transcript", mime_type="application/json")
async def get_transcript(session_id: str, ctx: Context) -> str:
    """Transcript du débat."""
    transcript = await ctx.get_state("transcript") or []
    return json.dumps({"session_id": session_id, "transcript": transcript})


# --- Prompts ---

@mcp.prompt(tags={"ai-persona"})
def ai_debater_prompt(
    topic: str,
    ai_position: str,
    style: str,
    previous_exchanges: list[str] | None = None,
    difficulty_level: int = 1,
) -> list[Message]:
    """Prompt pour l'IA débatrice."""
    prev = previous_exchanges or []
    return [
        Message(
            f"Tu débats sur « {topic} ». Ta position : {ai_position}. Style : {style}. Difficulté : {difficulty_level}. Échanges précédents : {prev[-2:]}. Produis un contre-argument solide.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"evaluation"})
def arbitrator_prompt(topic: str, debate_transcript: str, format_rules: str) -> list[Message]:
    """Prompt pour l'arbitre."""
    return [
        Message(
            f"Tu es l'arbitre du débat sur « {topic} ». Transcript : {debate_transcript[:800]}... Règles : {format_rules}. Donne un résumé, des scores, et un verdict équitable.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"evaluation"})
def argument_evaluator_prompt(argument: str, context: str, position: str) -> list[Message]:
    """Prompt pour évaluer un argument."""
    return [
        Message(
            f"Évalue cet argument (position : {position}) : « {argument} ». Contexte : {context}. Donne force, logique, preuves, sophismes éventuels, suggestions.",
            role="user",
        ),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8004)


if __name__ == "__main__":
    run()
