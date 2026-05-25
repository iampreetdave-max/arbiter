# When to Run the Judge Agent

## MANDATORY triggers -- run judge after EVERY:
- [ ] First deployment (live URL exists)
- [ ] First real user signs up
- [ ] First paying customer
- [ ] Every 10 new customers (10, 20, 30...)
- [ ] Each new major feature shipped (WhatsApp, Hindi, etc.)
- [ ] 2 weeks before Aug 17 deadline (Aug 3)
- [ ] 1 day before submission (Aug 16)

## HOW TO RUN
Spawn an Agent with:
- subagent_type: general-purpose
- prompt: Read .claude/prompts/judge_agent_prompt.md then execute it fully

## WHAT THE JUDGE UPDATES
- JUDGE_REPORT.md (scores, analysis, critical path)

## WHY THIS MATTERS
The judge score in JUDGE_REPORT.md is our compass.
If the score isn't going up, we're wasting time.
Business Viability is always the weakest -- focus there first.

## Current Score: 14/30 (2026-05-25)
Target Score:   28/30 (2026-08-10)
