"""
LearnForge MCP — Professor: Apprendre depuis une IA.
Profils : académique, terrain, mentor, vulgarisateur. Niveaux et styles.
"""
import json
from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Professor")

# --- Tools ---

@mcp.tool(tags={"session", "core"})
async def explain_concept(
    topic: Annotated[str, "Sujet ou concept à expliquer"],
    profile: Annotated[str, "academic | field_expert | mentor | vulgarizer"],
    level: Annotated[str, "beginner | intermediate | advanced"],
    style: Annotated[str, "analogies | pure_theory | concrete_examples"] = "concrete_examples",
    ctx: Context = CurrentContext(),
) -> str:
    """Demande une explication du concept selon le profil et le niveau choisis."""
    await ctx.set_state("current_profile", profile)
    await ctx.set_state("topic", topic)
    await ctx.set_state("level", level)
    await ctx.set_state("style", style)
    exchanges = await ctx.get_state("exchanges") or []
    exchanges.append({"role": "user", "content": f"Explique : {topic} (profil {profile}, niveau {level}, style {style})"})
    exchanges.append({"role": "assistant", "content": f"[Explication générée pour « {topic} » en mode {profile}, niveau {level}, avec {style}.]"})
    await ctx.set_state("exchanges", exchanges)
    await ctx.set_state("concepts_covered", await ctx.get_state("concepts_covered") or [])
    return f"Explication fournie pour « {topic} » (profil {profile}, niveau {level}). Vous pouvez poser des questions avec ask_followup."


@mcp.tool(tags={"session"})
async def change_profile(
    new_profile: Annotated[str, "academic | field_expert | mentor | vulgarizer"],
    ctx: Context = CurrentContext(),
) -> str:
    """Change le profil pédagogique et relance l'explication avec le nouveau profil."""
    await ctx.set_state("current_profile", new_profile)
    topic = await ctx.get_state("topic") or "sujet"
    return f"Profil changé en « {new_profile} ». Pour une nouvelle explication sur « {topic} », utilisez explain_concept avec ce profil."


@mcp.tool(tags={"session"})
async def ask_followup(
    question: Annotated[str, "Question de suivi"],
    ctx: Context = CurrentContext(),
) -> str:
    """Pose une question de suivi dans le cadre de la session en cours."""
    exchanges = await ctx.get_state("exchanges") or []
    exchanges.append({"role": "user", "content": question})
    exchanges.append({"role": "assistant", "content": f"[Réponse à la question : {question[:80]}...]"})
    await ctx.set_state("exchanges", exchanges)
    return f"Réponse enregistrée pour : « {question[:60]}... »"


@mcp.tool(tags={"session"})
async def request_example(
    concept: Annotated[str, "Concept pour lequel demander un exemple"],
    example_type: Annotated[str, "code | analogy | real_world | comparison"] = "real_world",
    ctx: Context = CurrentContext(),
) -> str:
    """Demande un exemple (code, analogie, cas concret ou comparaison) pour un concept."""
    return f"Exemple ({example_type}) pour « {concept} » : [contenu généré selon le type demandé]."


@mcp.tool(tags={"session", "output"})
async def generate_summary(ctx: Context = CurrentContext()) -> ToolResult:
    """Génère une synthèse de la session et les concepts clés."""
    topic = await ctx.get_state("topic") or "session"
    exchanges = await ctx.get_state("exchanges") or []
    concepts = await ctx.get_state("concepts_covered") or []
    summary_text = f"Synthèse de la session sur « {topic} » : {len(exchanges)} échanges. Concepts abordés : {concepts or ['voir échanges']}."
    return ToolResult(
        content=summary_text,
        structured_content={
            "topic": topic,
            "concepts_key": concepts,
            "exchange_count": len(exchanges),
            "level_attained": await ctx.get_state("level") or "intermediate",
        },
    )


# --- Resources ---

@mcp.resource("professor://profiles", mime_type="application/json")
def list_profiles() -> str:
    """Liste des 4 profils pédagogiques avec description et style."""
    data = [
        {"id": "academic", "description": "Professeur académique", "style": "Théorie structurée, définitions précises", "tone": "formel"},
        {"id": "field_expert", "description": "Expert terrain", "style": "Pratique, cas réels", "tone": "direct"},
        {"id": "mentor", "description": "Mentor", "style": "Guidance, questions réflexives", "tone": "bienveillant"},
        {"id": "vulgarizer", "description": "Vulgarisateur", "style": "Analogies, grand public", "tone": "accessible"},
    ]
    return json.dumps(data)


@mcp.resource("professor://profiles/{profile_id}", mime_type="application/json")
def get_profile(profile_id: str) -> str:
    """Détail d'un profil par ID."""
    profiles = {"academic": {"id": "academic", "description": "Professeur académique", "style": "Théorie structurée"}, "field_expert": {"id": "field_expert", "description": "Expert terrain"}, "mentor": {"id": "mentor", "description": "Mentor"}, "vulgarizer": {"id": "vulgarizer", "description": "Vulgarisateur"}}
    return json.dumps(profiles.get(profile_id, {}))


@mcp.resource("professor://levels", mime_type="application/json")
def list_levels() -> str:
    """Niveaux disponibles avec descriptifs."""
    data = [
        {"id": "beginner", "description": "Débutant", "detail": "Pas de prérequis"},
        {"id": "intermediate", "description": "Intermédiaire", "detail": "Bases acquises"},
        {"id": "advanced", "description": "Avancé", "detail": "Approfondissement"},
    ]
    return json.dumps(data)


@mcp.resource("professor://session/{session_id}", mime_type="application/json")
async def get_session(session_id: str, ctx: Context) -> str:
    """Transcript complet d'une session (par ID; état actuel si même session)."""
    exchanges = await ctx.get_state("exchanges") or []
    topic = await ctx.get_state("topic") or ""
    return json.dumps({"session_id": session_id, "topic": topic, "exchanges": exchanges})


# --- Prompts ---

@mcp.prompt(tags={"system"})
def academic_professor_prompt(topic: str, level: str, language: str = "fr") -> list[Message]:
    """Prompt professeur académique."""
    return [
        Message(f"Tu es un professeur académique. Explique le concept « {topic} » au niveau {level}, en {language}. Sois structuré et précis.", role="user"),
    ]


@mcp.prompt(tags={"system"})
def field_expert_prompt(topic: str, domain: str, years_experience: int = 10) -> list[Message]:
    """Prompt expert terrain."""
    return [
        Message(f"Tu es un expert terrain avec {years_experience} ans d'expérience en {domain}. Explique « {topic} » avec des cas concrets.", role="user"),
    ]


@mcp.prompt(tags={"system"})
def mentor_prompt(topic: str, learner_context: str = "") -> list[Message]:
    """Prompt mentor."""
    return [
        Message(f"Tu es un mentor. Guide l'apprenant sur « {topic} ». Contexte apprenant : {learner_context or 'non spécifié'}. Pose des questions pour faire réfléchir.", role="user"),
    ]


@mcp.prompt(tags={"system"})
def vulgarizer_prompt(topic: str, audience: str = "grand public") -> list[Message]:
    """Prompt vulgarisateur."""
    return [
        Message(f"Tu es un vulgarisateur. Explique « {topic} » pour un public {audience}, avec des analogies et sans jargon inutile.", role="user"),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8001)


if __name__ == "__main__":
    run()
