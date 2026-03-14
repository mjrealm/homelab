# Homelab Agents

This directory contains configurations and definitions for specialized AI **Agents** designed to manage distinct aspects of this homelab environment. These agents are built on the [Open Agent Skill Standard](https://agentskills.io/) and can be utilized by any compatible AI coding assistant, CLI, or IDE (such as Gemini, Antigravity, Claude Code, Cursor, Aider, OpenClaw, etc.).

> [!TIP]
> **TL;DR:**
> 1. Install all agents globally:
> ```bash
> cd agents/ && ./install.sh
> ```
> 2. Use in Gemini CLI: `gemini --skill homelab-admin "Update the peanut ingress"`
> 3. Use in Antigravity IDE: Type `@homelab-admin` in chat or say "Ask the homelab-admin to..."

## What is an Agent?

An agent (like the `admin` folder) represents a specific persona or role equipped with specialized instructions, workflows, and context for managing distinct parts of the homelab. An agent's directory organizes the specific "skills" and knowledge suited to its domain.

## How to Use These Agents

Because these agents follow the Open Agent Skill Standard, you can manually use them with any supporting AI tool by pointing it to the relevant `SKILL.md` file or directory.

### Automated Installation (Gemini & Antigravity)

If you are using Gemini CLI or Antigravity, you can use the provided `install.sh` script to automatically install all defined agents in this repository to your local environments:

```bash
cd agents/
./install.sh
```
*Note: This script will prefix the agent directories and their names with `homelab-` (e.g., `homelab-admin`) to prevent conflicts with other system skills.*

Alternatively, you can manually utilize these agents by placing them in the correct directories for your respective tools.

### For Gemini CLI

The Gemini CLI expects skills to be in a specific format within its configuration. To use an agent with Gemini CLI:
1. Ensure the agent folder is located at `~/.gemini/skills/<agent-name>` (or `~/.agents/skills/<agent-name>`). You can also use `gemini skills link /path/to/agents/my-skill` to automatically symlink it.
2. The agent must have a `SKILL.md` file with at least `name` and `description` in the YAML frontmatter.
3. In your prompt, ask the CLI to use the skill by name.

### For Antigravity

Antigravity expects skills to be located in `~/.gemini/antigravity/skills/<agent-name>/SKILL.md`. To use an agent within Antigravity directly from this workspace:

1. **Direct Instruction**: In your chat, explicitly ask the assistant to use a specific agent's context. 
   - *Example:* "Act as the homelab admin to help me troubleshoot the Kubernetes cluster."
2. **File References**: Use the `@` mention syntax or directly reference the agent's definition file so the assistant loads its instructions. 
   - *Example:* "Review the logs based on the guidelines in `@agents/admin/SKILL.md`."
3. **Contextual Awareness**: If you are actively working in or modifying files related to an agent's domain, Antigravity will automatically detect and reference its instructions (`SKILL.md`) and workflows to assist you accurately.

### For Other Tools (Cursor, Claude Code, Aider, etc.)

Check the documentation for your specific AI assistant on how it supports the Open Agent Skills standard. Generally, you can:
- Point the tool to the `agents/<agent-name>` directory.
- Manually inject the `SKILL.md` contents into your prompt or custom instructions.
- Use tools like the `agency-agents` converson scripts to translate the `SKILL.md` into tool-specific formatting (like `.cursorrules` or `.windsurfrules`).

## Agent Structure

This repository follows the [Open Agent Skill Standard](https://agentskills.io/). Each agent has its own directory (e.g., `agents/admin/`) containing:
- `SKILL.md` (required): The core instruction file with YAML frontmatter defining the agent's definition and markdown body containing standard operating procedures.
- `scripts/` (optional): Executable code, custom helper scripts, and tools for the agent's operations.
- `references/` (optional): Detailed technical reference, static documentation, or domain-specific files used by the agent (e.g., `REFERENCE.md`).
- `assets/` (optional): Templates (document or configuration templates), data files, or other resources.
- *(Note: `workflows/` is a custom addition in this repository for specific automated multi-step slash commands).*

## Creating a New Agent

To define a new agent for this repository using the standard:
1. Create a new directory under `agents/` named after the agent (e.g., `agents/network-engineer/`). The directory name must exactly match the `name` field in the frontmatter.
2. Add a `SKILL.md` file within that folder.
3. Include the standard YAML frontmatter:
   ```yaml
   ---
   name: network-engineer
   description: Your description of what this skill does and when to use it.
   license: Apache-2.0
   compatibility: Designed for Gemini CLI and Antigravity
   ---
   ```
   *(Note: `name` and `description` are the strict minimum required. `license`, `compatibility`, `metadata`, and `allowed-tools` are optional standard fields).*
4. Detail the agent's instructions, scope of work, and strict rules below the frontmatter.
5. Create standard subdirectories (`scripts/`, `references/`, `assets/`) if the agent requires them.
