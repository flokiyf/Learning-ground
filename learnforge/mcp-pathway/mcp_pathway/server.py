"""
LearnForge MCP — Pathway: Parcours guidé A→Z.
Curriculum, concepts, sources officielles, progression, révision espacée.
"""
import json
import hashlib
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP, Context
from fastmcp.dependencies import CurrentContext
from fastmcp.prompts import Message
from fastmcp.tools.tool import ToolResult

mcp = FastMCP("LearnForge Pathway")

# --- Tools ---

@mcp.tool(tags={"curriculum", "setup"}, timeout=30.0)
async def generate_curriculum(
    subject: Annotated[str, "Sujet ou domaine (ex: C#, Machine Learning)"],
    current_level: Annotated[str, "zero | beginner | intermediate | advanced"] = "zero",
    target_level: Annotated[str, "beginner | intermediate | advanced | expert"] = "advanced",
    duration_weeks: Annotated[int, Field(ge=2, le=52, description="Durée cible en semaines")] = 12,
    learning_style: Annotated[str, "balanced | theory_first | practice_first"] = "balanced",
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Génère un curriculum complet pour maîtriser un sujet de A à Z."""
    await ctx.report_progress(0, 100)
    curriculum_id = hashlib.sha256(f"{subject}:{current_level}:{target_level}".encode()).hexdigest()[:12]
    modules = [
        {"id": "m1", "title": f"Introduction à {subject}", "concepts": ["concept_1", "concept_2"], "prerequisites": [], "estimated_hours": 4, "official_sources": []},
        {"id": "m2", "title": f"Fondements {subject}", "concepts": ["concept_3", "concept_4"], "prerequisites": ["concept_1"], "estimated_hours": 8, "official_sources": []},
        {"id": "m3", "title": f"Pratique avancée", "concepts": ["concept_5", "concept_6"], "prerequisites": ["concept_3", "concept_4"], "estimated_hours": 12, "official_sources": []},
    ]
    all_concepts = []
    for m in modules:
        all_concepts.extend(m["concepts"])
    await ctx.set_state("curriculum_id", curriculum_id)
    await ctx.set_state("subject", subject)
    await ctx.set_state("modules", modules)
    await ctx.set_state("concept_scores", {c: None for c in all_concepts})
    await ctx.set_state("current_concept_index", 0)
    await ctx.report_progress(100, 100)
    return ToolResult(
        content=f"Curriculum généré pour « {subject} » : {len(modules)} modules, {len(all_concepts)} concepts.",
        structured_content={
            "curriculum_id": curriculum_id,
            "subject": subject,
            "modules": modules,
            "total_concepts": len(all_concepts),
            "recommended_modes": ["professor", "teacher", "jury"],
        },
    )


@mcp.tool(tags={"curriculum", "sources"}, timeout=20.0)
async def fetch_official_sources(
    concept: Annotated[str, "Nom du concept"],
    domain: Annotated[str, "Domaine (ex: csharp, python, javascript)"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Récupère les sources officielles recommandées pour un concept."""
    registry = {
        "csharp": ["learn.microsoft.com", "docs.microsoft.com/dotnet"],
        "python": ["docs.python.org", "peps.python.org"],
        "javascript": ["developer.mozilla.org", "tc39.es"],
    }
    base_urls = registry.get(domain.lower(), registry["python"])
    primary = {"title": f"Documentation officielle {domain}", "url": f"https://{base_urls[0]}", "type": "official_doc"}
    secondary = [{"title": f"Référence {domain}", "url": f"https://{base_urls[1]}", "type": "spec"}]
    return ToolResult(
        content=f"Sources officielles pour « {concept} » (domaine {domain}).",
        structured_content={
            "primary_source": primary,
            "secondary_sources": secondary,
            "exercises": [],
        },
    )


@mcp.tool(tags={"curriculum", "navigation"})
async def get_next_concept(ctx: Context = CurrentContext()) -> ToolResult:
    """Retourne le prochain concept à traiter dans le parcours."""
    modules = await ctx.get_state("modules")
    concept_scores = await ctx.get_state("concept_scores") or {}
    current_index = await ctx.get_state("current_concept_index") or 0
    if not modules:
        return ToolResult(content="Aucun curriculum actif. Appelez generate_curriculum d'abord.", structured_content={})
    all_concepts = []
    for m in modules:
        for c in m["concepts"]:
            all_concepts.append((m["id"], m["title"], c))
    if current_index >= len(all_concepts):
        return ToolResult(
            content="Parcours terminé.",
            structured_content={"concept_id": None, "progress_percentage": 100},
        )
    module_id, module_title, concept_id = all_concepts[current_index]
    total = len(all_concepts)
    progress_pct = int(100 * current_index / total) if total else 0
    return ToolResult(
        content=f"Prochain concept : {concept_id} (module « {module_title} »).",
        structured_content={
            "concept_id": concept_id,
            "title": concept_id.replace("_", " ").title(),
            "module": module_id,
            "module_title": module_title,
            "prerequisites_met": True,
            "suggested_mode": "professor",
            "official_sources": [],
            "estimated_time_minutes": 30,
            "progress_percentage": progress_pct,
        },
    )


@mcp.tool(tags={"curriculum", "progress"})
async def mark_concept_complete(
    concept_id: Annotated[str, "ID du concept terminé"],
    mastery_score: Annotated[float, Field(ge=0.0, le=100.0, description="Score de maîtrise 0-100")],
    mode_used: Annotated[str, "professor | teacher | jury | debate | socratic | simulation"],
    ctx: Context = CurrentContext(),
) -> ToolResult:
    """Marque un concept comme complété et met à jour la progression."""
    concept_scores = await ctx.get_state("concept_scores") or {}
    concept_scores[concept_id] = mastery_score
    await ctx.set_state("concept_scores", concept_scores)
    current_index = await ctx.get_state("current_concept_index") or 0
    await ctx.set_state("current_concept_index", current_index + 1)
    modules = await ctx.get_state("modules") or []
    all_concepts = []
    for m in modules:
        all_concepts.extend(m["concepts"])
    total = len(all_concepts)
    next_index = current_index + 1
    next_concept_id = all_concepts[next_index] if next_index < total else None
    progress_pct = int(100 * (next_index) / total) if total else 100
    milestone = progress_pct in (25, 50, 75, 100)
    return ToolResult(
        content=f"Concept « {concept_id} » marqué complété (score {mastery_score}). Progression : {progress_pct}%.",
        structured_content={
            "next_concept_id": next_concept_id,
            "progress_percentage": progress_pct,
            "milestone_reached": milestone,
            "spaced_review_scheduled": [concept_id] if mastery_score < 80 else [],
        },
    )


@mcp.tool(tags={"curriculum", "progress"})
async def get_progress_overview(ctx: Context = CurrentContext()) -> ToolResult:
    """Vue d'ensemble de la progression du parcours actif."""
    curriculum_id = await ctx.get_state("curriculum_id")
    subject = await ctx.get_state("subject")
    modules = await ctx.get_state("modules") or []
    concept_scores = await ctx.get_state("concept_scores") or {}
    current_index = await ctx.get_state("current_concept_index") or 0
    if not curriculum_id:
        return ToolResult(content="Aucun curriculum actif.", structured_content={})
    total_concepts = sum(len(m["concepts"]) for m in modules)
    mastered = sum(1 for c, s in concept_scores.items() if s is not None and s >= 70)
    overall_pct = int(100 * mastered / total_concepts) if total_concepts else 0
    module_stats = []
    for m in modules:
        cs = [c for c in m["concepts"] if concept_scores.get(c) is not None and concept_scores.get(c) >= 70]
        module_stats.append({
            "id": m["id"],
            "title": m["title"],
            "completion": int(100 * len(cs) / len(m["concepts"])) if m["concepts"] else 0,
            "concepts_mastered": len(cs),
            "total_concepts": len(m["concepts"]),
        })
    return ToolResult(
        content=f"Parcours « {subject} » : {overall_pct}% complété ({mastered}/{total_concepts} concepts).",
        structured_content={
            "curriculum_id": curriculum_id,
            "subject": subject,
            "overall_percentage": overall_pct,
            "modules": module_stats,
            "knowledge_graph": {"nodes": list(concept_scores.keys()), "edges": []},
        },
    )


@mcp.tool(tags={"curriculum", "review"})
async def suggest_review_concepts(ctx: Context = CurrentContext()) -> ToolResult:
    """Suggère les concepts à réviser (répétition espacée)."""
    concept_scores = await ctx.get_state("concept_scores") or {}
    due = [
        {"concept_id": c, "last_score": s, "days_since": 7, "priority": "high" if s and s < 70 else "medium"}
        for c, s in concept_scores.items() if s is not None
    ][:5]
    return ToolResult(
        content=f"{len(due)} concept(s) suggérés pour révision." if due else "Aucune révision requise pour l'instant.",
        structured_content={"due_for_review": due},
    )


@mcp.tool(tags={"curriculum", "integration"})
async def link_mode_to_concept(
    concept_id: Annotated[str, "ID du concept"],
    mode: Annotated[str, "professor | teacher | jury | debate | socratic | simulation"],
    session_id: Annotated[str, "ID de la session"],
    performance_score: Annotated[float, Field(ge=0.0, le=100.0)],
    ctx: Context = CurrentContext(),
) -> str:
    """Lie un résultat de session à un concept du parcours."""
    links = await ctx.get_state("concept_session_links") or []
    links.append({"concept_id": concept_id, "mode": mode, "session_id": session_id, "performance_score": performance_score})
    await ctx.set_state("concept_session_links", links)
    return f"Session {session_id} liée au concept « {concept_id} » (mode {mode}, score {performance_score})."


# --- Resources ---

@mcp.resource("pathway://sources/{domain}", mime_type="application/json")
def get_source_registry(domain: str) -> str:
    """Registre des sources officielles par domaine."""
    registry = {
        "csharp": ["learn.microsoft.com", "docs.microsoft.com/dotnet"],
        "javascript": ["developer.mozilla.org", "tc39.es"],
        "python": ["docs.python.org", "peps.python.org"],
    }
    return json.dumps(registry.get(domain.lower(), registry["python"]))


@mcp.resource("pathway://curriculum/{curriculum_id}", mime_type="application/json")
async def get_curriculum(curriculum_id: str, ctx: Context) -> str:
    """Détail d'un curriculum par ID."""
    cid = await ctx.get_state("curriculum_id")
    if cid != curriculum_id:
        return json.dumps({"error": "curriculum not found or not active"})
    modules = await ctx.get_state("modules") or []
    subject = await ctx.get_state("subject") or "unknown"
    return json.dumps({"curriculum_id": curriculum_id, "subject": subject, "modules": modules})


@mcp.resource("pathway://curriculum/{curriculum_id}/concepts", mime_type="application/json")
async def get_concepts(curriculum_id: str, ctx: Context) -> str:
    """Liste des concepts d'un curriculum."""
    cid = await ctx.get_state("curriculum_id")
    if cid != curriculum_id:
        return json.dumps({"concepts": []})
    modules = await ctx.get_state("modules") or []
    concepts = []
    for m in modules:
        concepts.extend(m["concepts"])
    return json.dumps({"concepts": concepts})


@mcp.resource("pathway://curriculum/{curriculum_id}/progress", mime_type="application/json")
async def get_progress(curriculum_id: str, ctx: Context) -> str:
    """Progression d'un curriculum."""
    cid = await ctx.get_state("curriculum_id")
    if cid != curriculum_id:
        return json.dumps({"progress_percentage": 0})
    concept_scores = await ctx.get_state("concept_scores") or {}
    modules = await ctx.get_state("modules") or []
    total = sum(len(m["concepts"]) for m in modules)
    mastered = sum(1 for s in concept_scores.values() if s is not None and s >= 70)
    pct = int(100 * mastered / total) if total else 0
    return json.dumps({"progress_percentage": pct, "concept_scores": concept_scores})


@mcp.resource("pathway://templates/{subject_type}", mime_type="application/json")
def get_curriculum_template(subject_type: str) -> str:
    """Templates de curriculum par type de sujet."""
    templates = {
        "programming_language": {"steps": ["syntax", "types", "control_flow", "functions", "oop", "stdlib"]},
        "framework": {"steps": ["setup", "core_concepts", "routing", "state", "deployment"]},
        "domain_knowledge": {"steps": ["basics", "intermediate", "advanced", "practice"]},
        "soft_skill": {"steps": ["theory", "examples", "roleplay", "feedback"]},
    }
    return json.dumps(templates.get(subject_type, templates["domain_knowledge"]))


# --- Prompts ---

@mcp.prompt(tags={"curriculum-generation"})
def curriculum_generator_prompt(
    subject: str,
    current_level: str,
    target_level: str,
    duration_weeks: int,
    domain_context: str = "",
) -> list[Message]:
    """Génère un curriculum structuré avec séquençage logique."""
    return [
        Message(
            f"Génère un plan d'apprentissage pour « {subject} » : niveau actuel {current_level}, objectif {target_level}, "
            f"sur {duration_weeks} semaines. Contexte domaine : {domain_context or 'non spécifié'}.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"curriculum-generation"})
def concept_prerequisites_prompt(concept: str, domain: str, curriculum_context: str) -> list[Message]:
    """Identifie les prérequis d'un concept."""
    return [
        Message(
            f"Quels sont les prérequis pour maîtriser le concept « {concept} » dans le domaine {domain} ? Contexte : {curriculum_context}.",
            role="user",
        ),
    ]


@mcp.prompt(tags={"sources"})
def source_finder_prompt(concept: str, domain: str, level: str) -> list[Message]:
    """Trouve les sources officielles pour un concept."""
    return [
        Message(
            f"Trouve les sources officielles et à jour pour apprendre « {concept} » (domaine {domain}, niveau {level}).",
            role="user",
        ),
    ]


@mcp.prompt(tags={"review"})
def spaced_review_prompt(
    concept: str,
    last_session_summary: str,
    days_since_last_review: int,
) -> list[Message]:
    """Prépare une micro-session de révision espacée."""
    return [
        Message(
            f"Révision du concept « {concept} ». Résumé dernière session : {last_session_summary}. "
            f"Jours depuis dernière révision : {days_since_last_review}. Propose des questions de révision.",
            role="user",
        ),
    ]


def run() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8007)


if __name__ == "__main__":
    run()
