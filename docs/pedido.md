# Requesting an asset

The form the game agent fills in to ask the engine for an asset. Generated from the skill
(`.claude/skills/pixel-asset-engine/SKILL.md`) by `scripts/skill.py`; do not edit here.

- **Verb:** create (a new asset), complete (what an asset lacks: a clip, a requested view) or fix (an asset drawn
  wrong).
- **What:** the type (object, building, tree, shrub, human, quadruped), its role in the game, whether it walks or is
  static, and the size (the category from the size table, or the height in metres).
- **Where:** the place in the game (the edge of a field, a yard, a house), which tells the climate and the wear.
- **Reference:** the species, the model or the image, if any.
