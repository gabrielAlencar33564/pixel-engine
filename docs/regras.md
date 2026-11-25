# Engine rules

The single source of the rules that did not become checks. `CLAUDE.md`, `AGENTS.md` and the skill cite this file and
repeat nothing from it. What can be checked is a test, not a line here.

## What the engine is

- The engine is an AI's hand for pixel art: the AI describes the asset as data, and the engine draws, checks and
  exports.
- The game agent asks (create, complete, fix) and assembles the scenes; the engine authors and delivers, without
  assembling a scene or a game.

## Drawing

- Shape before colour: a weak delivery is fixed in the construction (pieces, measurements, primitives), not by
  swapping tones.
- A concrete reference before drawing: the sheet cites the source, the real measurements and what gives the thing
  life; it informs the data and never becomes a 2D cut-out.
- Anatomy against the reference: if the rig cannot do the pose, say so before drawing.
- Creation, not reuse: a new asset is born from its own sheet, not from a stretched example.
- Size comes from real metres at the world scale, never from the canvas.
- A solution is measured in the sprite's final pixel and in its cost, not in a sophisticated 3D render.
- A character is a figure for the top-down camera, with few pixels: simple shapes the AI can predict in the pixel
  (the head is an egg), not real anatomy. The real body gives the overall proportions; detail that does not show in
  the sprite (the nose, the chin, the skull) is not modelled: it only distorts.

## Limits and fixes

- Stop rather than make it worse: if a limit forces a visible loss of quality, fix the cause in the engine (the
  piece, the limit), never the drawing, and show the before and after.
- Training fixes the engine: a failure that an asset exposes becomes a general capability, proven by a synthetic
  fixture with a negative control; never a patch on the asset, and the training asset does not stay in the repository.
- One factor at a time, with before and after side by side before declaring an improvement.
- A fix only counts when the engine refuses the old way or when the old way no longer exists.

## Art and approval

- Only the owner approves art: `art_review` changes only through a recorded human review.
- Nobody approves their own work: done comes from a proof made by someone who did not write the code.

## Work

- Only one session writes to this repository at a time.
- Images: read the numbers first; the sheet is the real-size crop, enlarged at most 4×.
- A decision the plan does not fix goes in one line in `docs/decisoes.md`; the why goes in the commit.
- Each verified step becomes a small commit on `main`, without asking; push only when the owner asks.
- The working asset store and the builds stay out of git.
