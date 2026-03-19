---
name: skiller:analyze-consented-permissions
description: Analyze permission grant patterns across sessions and suggest auto-allow configurations
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"]
disable-model-invocation: true
---

CRITICAL INSTRUCTION: Before doing ANYTHING else, you MUST call the Skill tool with:
  Skill(skill="skiller:permission-consent-analyzer")

Do NOT read files, explore code, or generate any response before invoking this skill.
