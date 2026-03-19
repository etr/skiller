---
name: skiller:analyze-gaps
description: Analyze instrumented sessions for behavioral gaps and generate improvement suggestions
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "Agent", "Skill"]
disable-model-invocation: true
---

CRITICAL INSTRUCTION: Before doing ANYTHING else, you MUST call the Skill tool with:
  Skill(skill="skiller:gap-analyzer")

Do NOT read files, explore code, or generate any response before invoking this skill.
