# LearnForge MCP Servers

7 serveurs MCP FastMCP pour l'apprentissage (professeur, teacher, jury, débat, socratique, simulation, pathway).

## Installation

```bash
pip install -e learnforge/mcp-professor learnforge/mcp-pathway learnforge/mcp-teacher learnforge/mcp-jury learnforge/mcp-debate learnforge/mcp-socratic learnforge/mcp-simulation
```

## Lancer un serveur

```bash
python -m mcp_professor.server   # port 8001
python -m mcp_pathway.server     # port 8007
# etc.
```
