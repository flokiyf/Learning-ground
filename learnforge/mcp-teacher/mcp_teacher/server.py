"""
LearnForge MCP — Teacher: Enseigner à un groupe d'étudiants IA (méthode Feynman).
Personnalités : curieux, sceptique, rapide, silencieux. Réactions et demande de démo code.
"""
import json
import uuid
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Teacher")

# --- Tools ---

@mcp.tool(tags={"session", "setup"}, timeout=10.0)
async def create_classroom(
    topic: Annotated[str, "Sujet à expliquer aux étudiants"],
    num_students: Annotated[int, Field(ge=2, le=5, description="Nombre d'étudiants (2-5)")] = 3,
    difficulty: Annotated[str, "beginner | mixed | advanced"] = "mixed",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Crée une classe virtuelle avec des étudiants IA aux personnalités distinctes."""
    personalities = ["curious", "skeptic", "fast_learner", "silent", "perfectionist"]
    students = []
    for i in range(num_students):
        pid = personalities[i % len(personalities)]
        students.append({
            "id": f"stu_{uuid.uuid4().hex[:8]}",
            "name": f"Étudiant {i+1}",
            "personality": pid,
            "avatar_emoji": ["🔍", "🤔", "🚀", "😶", "✏️"][i % 5],
        })
    await ctx.set_state("topic", topic)
    await ctx.set_state("students", {s["id"]: {"personality": s["personality"], "confusion_level": 0, "questions_asked": 0, "satisfaction": 50} for s in students})
    await ctx.set_state("user_explanations", [])
    await ctx.set_state("session_phase", "explaining")
    await ctx.set_state("feynman_indicators", {"clarity": 0, "depth": 0, "examples": 0, "handling_questions": 0})
    return ToolResult(
        content=f"Classe créée pour « {topic} » avec {num_students} étudiants. Vous pouvez expliquer ; ils réagiront avec student_react.",
        structured_content={"students": students},
    )


@mcp.tool(tags={"session", "core"})
async def student_react(
    student_id: Annotated[str, "ID de l'étudiant"],
    trigger: Annotated[str, "explanation_received | concept_unclear | wants_more | confused"],
    user_explanation: Annotated[str, "Explication que vous venez de donner"],
    ctx: Context = CurrentContext(),
) -> str:
    """Simule la réaction d'un étudiant après votre explication."""
    students = await ctx.get_state("students") or {}
    if student_id not in students:
        return f"Étudiant {student_id} inconnu."
    st = students[student_id]
    st["questions_asked"] = st.get("questions_asked", 0) + 1
    if trigger == "concept_unclear":
        st["confusion_level"] = min(100, st.get("confusion_level", 0) + 20)
    await ctx.set_state("students", students)
    reactions = {"explanation_received": "D'accord, je vois mieux.", "concept_unclear": "Je ne vois pas bien le lien avec...", "wants_more": "Tu peux aller plus loin sur ce point ?", "confused": "Attends, ça contredit un peu ce que tu disais avant."}
    return f"[{student_id}] {reactions.get(trigger, 'Hmm.')}"


@mcp.tool(tags={"session", "core"})
async def answer_student_question(
    student_id: Annotated[str, "ID de l'étudiant"],
    answer: Annotated[str, "Votre réponse à sa question"],
    ctx: Context = CurrentContext(),
) -> str:
    """Enregistre votre réponse à une question d'étudiant et retourne sa réaction."""
    students = await ctx.get_state("students") or {}
    if student_id not in students:
        return f"Étudiant {student_id} inconnu."
    st = students[student_id]
    st["satisfaction"] = min(100, st.get("satisfaction", 50) + 10)
    st["confusion_level"] = max(0, st.get("confusion_level", 0) - 15)
    await ctx.set_state("students", students)
    return f"[{student_id}] Merci, c'est plus clair maintenant."


@mcp.tool(tags={"session", "core"})
async def request_code_demo(
    student_id: Annotated[str, "ID de l'étudiant"],
    concept: Annotated[str, "Concept pour lequel il demande une démo code"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Un étudiant demande une démonstration en code ; signale au client d'activer l'éditeur de code."""
    return ToolResult(
        content=f"L'étudiant {student_id} demande une démo code pour « {concept} ». Activez l'éditeur de code côté client.",
        structured_content={
            "action": "activate_code_editor",
            "language": "python",
            "prompt": f"Montre-moi un exemple de code pour : {concept}",
        },
    )


@mcp.tool(tags={"session", "output"})
async def end_session(ctx: Context = CurrentContext()) -> ToolResult:
    """Termine la session et retourne le score Feynman et les recommandations."""
    students = await ctx.get_state("students") or {}
    indicators = await ctx.get_state("feynman_indicators") or {}
    satisfaction_avg = sum(s.get("satisfaction", 0) for s in students.values()) / len(students) if students else 0
    feynman_score = min(100, int(satisfaction_avg + sum(indicators.values())))
    return ToolResult(
        content=f"Session terminée. Score Feynman : {feynman_score}/100.",
        structured_content={
            "feynman_score": feynman_score,
            "strengths": ["Clarté", "Exemples"] if feynman_score >= 60 else [],
            "gaps": ["Approfondir les cas limites"] if feynman_score < 70 else [],
            "recommendation": "Réessayer avec un autre angle ou plus d'exemples." if feynman_score < 70 else "Bien maîtrisé pour cette session.",
        },
    )


# --- Resources ---

@mcp.resource("teacher://students/profiles", mime_type="application/json")
def list_student_profiles() -> str:
    """Profils des personnalités d'étudiants (curious, skeptic, fast_learner, silent, perfectionist)."""
    data = [
        {"id": "curious", "description": "Pose toujours des questions de base", "behavior": "Demande des exemples"},
        {"id": "skeptic", "description": "Doute et demande des preuves", "behavior": "Conteste gentiment"},
        {"id": "fast_learner", "description": "Veut aller plus loin", "behavior": "Demande des cas avancés"},
        {"id": "silent", "description": "Ne comprend pas mais n'ose pas demander", "behavior": "Réagit peu"},
        {"id": "perfectionist", "description": "Veut les détails parfaits", "behavior": "Pinaillage"},
    ]
    return json.dumps(data)


@mcp.resource("teacher://students/{student_id}/state", mime_type="application/json")
async def get_student_state(student_id: str, ctx: Context) -> str:
    """État actuel de compréhension d'un étudiant."""
    students = await ctx.get_state("students") or {}
    st = students.get(student_id, {"confusion_level": 0, "questions_asked": 0, "satisfaction": 50})
    return json.dumps({"student_id": student_id, "comprehension": 100 - st.get("confusion_level", 0), **st})


@mcp.resource("teacher://evaluation/feynman-criteria", mime_type="application/json")
def get_feynman_criteria() -> str:
    """Grille d'évaluation Feynman : clarté, analogies, profondeur, gestion des questions."""
    data = {"criteria": ["clarity", "analogies", "depth", "handling_questions"], "description": "Évaluation méthode Feynman"}
    return json.dumps(data)


@mcp.resource("teacher://session/{session_id}/log", mime_type="application/json")
async def get_session_log(session_id: str, ctx: Context) -> str:
    """Journal de la session (explications et réactions)."""
    explanations = await ctx.get_state("user_explanations") or []
    students = await ctx.get_state("students") or {}
    return json.dumps({"session_id": session_id, "user_explanations": explanations, "students_state": students})


# --- Prompts ---

@mcp.prompt(tags={"student-persona"})
def curious_student_prompt(topic: str, current_confusion: str = "") -> list[Message]:
    """Persona étudiant curieux."""
    return [Message(f"Tu es un étudiant curieux. Sujet : {topic}. Confusion actuelle : {current_confusion or 'aucune'}. Pose une question de base.", role="user")]


@mcp.prompt(tags={"student-persona"})
def skeptic_student_prompt(topic: str, claimed_fact: str = "") -> list[Message]:
    """Persona étudiant sceptique."""
    return [Message(f"Tu es un étudiant sceptique. Sujet : {topic}. L'enseignant a dit : {claimed_fact or '—'}. Demande une preuve ou un contre-exemple.", role="user")]


@mcp.prompt(tags={"student-persona"})
def fast_learner_prompt(topic: str, already_knows: str = "") -> list[Message]:
    """Persona étudiant rapide."""
    return [Message(f"Tu es un étudiant qui va vite. Sujet : {topic}. Tu sais déjà : {already_knows or '—'}. Demande d'aller plus loin.", role="user")]


@mcp.prompt(tags={"student-persona"})
def silent_confused_prompt(topic: str, confusion_point: str = "") -> list[Message]:
    """Persona étudiant silencieux mais confus."""
    return [Message(f"Tu es un étudiant qui n'ose pas demander. Sujet : {topic}. Point de confusion : {confusion_point or '—'}. Formule une question timide.", role="user")]


@mcp.prompt(tags={"evaluation"})
def feynman_evaluation_prompt(topic: str, session_transcript: str, student_reactions: list[str]) -> list[Message]:
    """Évaluation Feynman de la session."""
    return [
        Message(
            f"Évalue la session d'enseignement sur « {topic} ». Transcript : {session_transcript[:500]}... Réactions étudiants : {student_reactions}. Donne un score Feynman et des recommandations.",
            role="user",
        ),
    ]


def run() -> None:
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8002)


if __name__ == "__main__":
    run()
