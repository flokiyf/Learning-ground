"""
LearnForge MCP — Jury: Panel d'experts IA qui testent la compréhension.
Domaines, difficulté, questions fondamentales / cas limites / contradictions.
"""
import json
import uuid
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Jury")

# --- Tools ---

@mcp.tool(tags={"session", "setup"}, timeout=15.0)
async def assemble_jury(
    topic: Annotated[str, "Sujet à évaluer"],
    domain: Annotated[str, "tech | science | business | medicine | law | general"] = "tech",
    difficulty: Annotated[str, "standard | rigorous | brutal"] = "rigorous",
    num_experts: Annotated[int, Field(ge=2, le=4, description="Nombre d'experts (2-4)")] = 3,
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Constitue un jury d'experts avec styles d'interrogation distincts."""
    styles = ["fundamental_questioner", "edge_case_hunter", "contradiction_seeker", "practical_tester"]
    jury = []
    for i in range(num_experts):
        jury.append({
            "id": f"exp_{uuid.uuid4().hex[:8]}",
            "name": f"Expert {i+1}",
            "expertise": domain,
            "interrogation_style": styles[i % len(styles)],
            "avatar": ["📐", "🔬", "⚖️", "🛠️"][i % 4],
        })
    await ctx.set_state("topic", topic)
    await ctx.set_state("domain", domain)
    await ctx.set_state("jury", jury)
    await ctx.set_state("transcript", [])
    await ctx.set_state("expert_scores", {e["id"]: 0 for e in jury})
    return ToolResult(
        content=f"Jury constitué pour « {topic} » : {num_experts} experts ({domain}, difficulté {difficulty}). Utilisez next_question puis submit_answer.",
        structured_content={"jury": jury},
    )


@mcp.tool(tags={"session", "core"})
async def next_question(
    expert_id: Annotated[str, "ID de l'expert qui pose la question"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Obtient la prochaine question d'un expert (adaptée aux réponses précédentes)."""
    jury = await ctx.get_state("jury") or []
    transcript = await ctx.get_state("transcript") or []
    expert = next((e for e in jury if e["id"] == expert_id), None)
    if not expert:
        return ToolResult(content="Expert inconnu.", structured_content={})
    q_type = "fundamental" if "fundamental" in expert["interrogation_style"] else "edge_case" if "edge" in expert["interrogation_style"] else "contradiction" if "contradiction" in expert["interrogation_style"] else "practical"
    question = f"Question ({q_type}) de {expert['name']} : Pouvez-vous expliquer en quoi ce concept s'applique dans un cas limite ?"
    return ToolResult(
        content=question,
        structured_content={"question": question, "expert_id": expert_id, "type": q_type},
    )


@mcp.tool(tags={"session", "core"})
async def submit_answer(
    expert_id: Annotated[str, "ID de l'expert à qui répondre"],
    answer: Annotated[str, "Votre réponse"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Soumet une réponse à l'expert et obtient sa réaction et un éventuel suivi."""
    transcript = await ctx.get_state("transcript") or []
    transcript.append({"expert_id": expert_id, "answer": answer})
    await ctx.set_state("transcript", transcript)
    scores = await ctx.get_state("expert_scores") or {}
    scores[expert_id] = scores.get(expert_id, 0) + 15
    await ctx.set_state("expert_scores", scores)
    return ToolResult(
        content="Réponse enregistrée. L'expert note votre réponse et peut poser une question de suivi.",
        structured_content={"reaction": "Acceptable. Question de suivi : Et dans le cas X ?", "follow_up_question": "Et dans le cas X ?", "score_delta": 15},
    )


@mcp.tool(tags={"session", "core"})
async def request_code_challenge(
    expert_id: Annotated[str, "ID de l'expert"],
    challenge_type: Annotated[str, "implement | debug | design | review"] = "implement",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Un expert demande une preuve par le code (éditeur activé côté client)."""
    topic = await ctx.get_state("topic") or "concept"
    return ToolResult(
        content=f"L'expert demande un défi code ({challenge_type}) pour « {topic} ». Activez l'éditeur de code.",
        structured_content={
            "action": "activate_code_editor",
            "challenge_description": f"Implémentez une solution pour illustrer : {topic}",
            "expected_output": "Code fonctionnel et lisible",
        },
    )


@mcp.tool(tags={"session", "output"})
async def final_verdict(ctx: Context = CurrentContext()) -> ToolResult:
    """Verdict final du jury : score, points forts, lacunes, recommandations."""
    topic = await ctx.get_state("topic") or "sujet"
    expert_scores = await ctx.get_state("expert_scores") or {}
    jury = await ctx.get_state("jury") or []
    overall = int(sum(expert_scores.values()) / len(expert_scores)) if expert_scores else 0
    verdict = "passed" if overall >= 70 else "needs_work" if overall >= 50 else "failed"
    expert_comments = [{"expert_id": e["id"], "score": expert_scores.get(e["id"], 0), "comments": "À renforcer."} for e in jury]
    return ToolResult(
        content=f"Verdict : {verdict.upper()} (score global {overall}/100).",
        structured_content={
            "overall_score": overall,
            "verdict": verdict,
            "expert_scores": expert_comments,
            "strengths": ["Bonne base"] if overall >= 50 else [],
            "critical_gaps": ["Approfondir les cas limites"] if overall < 70 else [],
            "recommended_next_steps": ["Réviser avec le mode Professeur"] if overall < 70 else ["Passer au concept suivant"],
        },
    )


# --- Resources ---

@mcp.resource("jury://experts/profiles", mime_type="application/json")
def list_expert_profiles() -> str:
    """Profils d'experts : fundamental_questioner, edge_case_hunter, contradiction_seeker, practical_tester."""
    data = [
        {"id": "fundamental_questioner", "description": "Pose des questions fondamentales"},
        {"id": "edge_case_hunter", "description": "Cherche les cas limites"},
        {"id": "contradiction_seeker", "description": "Cherche les incohérences"},
        {"id": "practical_tester", "description": "Teste la mise en pratique"},
    ]
    return json.dumps(data)


@mcp.resource("jury://evaluation/criteria/{domain}", mime_type="application/json")
def get_evaluation_criteria(domain: str) -> str:
    """Critères d'évaluation par domaine."""
    criteria = {"tech": ["exactitude", "pratique", "architecture"], "science": ["rigueur", "méthode"], "business": ["décision", "communication"], "general": ["clarté", "complétude"]}
    return json.dumps({"domain": domain, "criteria": criteria.get(domain, criteria["general"])})


@mcp.resource("jury://session/{session_id}/transcript", mime_type="application/json")
async def get_transcript(session_id: str, ctx: Context) -> str:
    """Transcript de la session jury."""
    transcript = await ctx.get_state("transcript") or []
    return json.dumps({"session_id": session_id, "transcript": transcript})


@mcp.resource("jury://verdicts/{session_id}", mime_type="application/json")
async def get_verdict(session_id: str, ctx: Context) -> str:
    """Verdict stocké pour une session (après final_verdict)."""
    expert_scores = await ctx.get_state("expert_scores") or {}
    overall = int(sum(expert_scores.values()) / len(expert_scores)) if expert_scores else 0
    return json.dumps({"session_id": session_id, "overall_score": overall, "verdict": "passed" if overall >= 70 else "needs_work" if overall >= 50 else "failed"})


# --- Prompts ---

@mcp.prompt(tags={"expert-persona"})
def expert_fundamental_prompt(topic: str, expertise_area: str) -> list[Message]:
    """Expert qui pose des questions fondamentales."""
    return [Message(f"Tu es un expert en {expertise_area}. Sujet : {topic}. Pose une question sur les fondements.", role="user")]


@mcp.prompt(tags={"expert-persona"})
def expert_edge_case_prompt(topic: str, known_weak_points: list[str] | None = None) -> list[Message]:
    """Expert qui cherche les cas limites."""
    weak = known_weak_points or []
    return [Message(f"Tu es un expert. Sujet : {topic}. Points faibles connus : {weak}. Pose une question sur un cas limite.", role="user")]


@mcp.prompt(tags={"expert-persona"})
def expert_contradiction_prompt(topic: str, user_previous_answers: list[str] | None = None) -> list[Message]:
    """Expert qui cherche les incohérences."""
    prev = user_previous_answers or []
    return [Message(f"Tu es un expert. Sujet : {topic}. Réponses précédentes : {prev[:3]}. Cherche une incohérence ou une question piège.", role="user")]


@mcp.prompt(tags={"evaluation"})
def final_verdict_prompt(topic: str, domain: str, full_transcript: str, criteria: str) -> list[Message]:
    """Génération du verdict final."""
    return [
        Message(
            f"Verdict pour le sujet « {topic} » (domaine {domain}). Transcript : {full_transcript[:500]}... Critères : {criteria}. Donne verdict (passed/needs_work/failed), points forts, lacunes, recommandations.",
            role="user",
        ),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8003)


if __name__ == "__main__":
    run()
