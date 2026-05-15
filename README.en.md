# RaySkills

**English | [繁體中文](./README.md)**

Ray's personal AI Agent skill library — a collection of reusable skills for Claude, GitHub Copilot CLI, OpenAI Codex, and any other AI agent that supports skill/instruction mechanisms.

## What is a Skill?

A skill is a `SKILL.md` file that tells an AI agent what to do and when to do it. When you say something that matches a skill's description, the agent automatically loads the corresponding instructions, templates, and tools.

- **frontmatter** (`name` + `description`): trigger condition, always in context
- **SKILL.md body**: detailed instructions, loaded when triggered
- **scripts / references / assets**: supporting resources, loaded on demand

## Skill List

| Skill | Description | Trigger phrases |
|-------|-------------|-----------------|
| [skill-creator](./skill-creator/) | Create, improve, or optimize skills | "help me create a skill", "wrap this workflow into a skill" |
| [presentation-builder](./presentation-builder/) | Build slides from any source material | "make me a presentation", "turn these notes into slides" |

## Usage

### Using in Claude / Copilot CLI

1. Add the skill to your `.claude/commands/` directory, or ensure the Copilot CLI can discover these skills
2. Say a trigger phrase — the skill loads automatically

### Adding a New Skill

Use the `skill-creator` skill:

```
Help me create a skill for...
```

Or manually:
1. Create a directory at `RaySkills/<skill-name>/`
2. Write a `SKILL.md` (refer to existing skills for format)
3. Validate the structure with `quick_validate`:
   ```bash
   cd skill-creator
   python -m scripts.quick_validate ../<skill-name>
   ```

### Optimizing Skill Trigger Descriptions

```bash
cd skill-creator
python -m scripts.run_loop \
  --eval-set ../<skill-name>/evals/trigger_evals.json \
  --skill-path ../<skill-name> \
  --model claude-sonnet-4-5 \
  --verbose
```

## Requirements

- Python 3.9+ (3.13 recommended)
- `claude` CLI (for description optimization loop)
- Marp CLI (for presentation-builder slide export)
- Chrome / Chromium / Edge (required for Marp PDF/PPTX export)

## License

[Apache License 2.0](./LICENSE) © 2026 Ray Chen
