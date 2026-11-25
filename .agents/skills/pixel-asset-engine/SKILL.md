---
name: pixel-asset-engine
description: Creates, completes and fixes game pixel-art assets (prop, flora, building, human, quadruped) with the local `pfe` engine, from the request to the verified export, in the asset store and with no game project.
---

# Pixel Asset Engine: from request to export

The drawing and working rules are in `docs/regras.md`; read them first. This is the path. The engine is the hand: you
describe the asset as data (the **composition**), and it draws, checks and exports. Run everything from the engine
folder with `uv run pfe ...` (or `.venv/Scripts/pfe.exe` on Windows), always with `--json`. Identifiers (pieces,
arguments, JSON keys, commands, codes) are in Portuguese: use them exactly as written.

## 1. The request

The game agent asks with this form (also in `docs/pedido.md`):

<!-- pedido -->
- **Verb:** create (a new asset), complete (what an asset lacks: a clip, a requested view) or fix (an asset drawn
  wrong).
- **What:** the type (object, building, tree, shrub, human, quadruped), its role in the game, whether it walks or is
  static, and the size (the category from the size table, or the height in metres).
- **Where:** the place in the game (the edge of a field, a yard, a house), which tells the climate and the wear.
- **Reference:** the species, the model or the image, if any.
<!-- /pedido -->

## 2. The reference sheet

Before composing, write the sheet in the composition's `reference` field: the concrete reference (species, model,
period), the real measurements in metres, and what gives the thing life (the wide low crown, the worn thatch, the
swinging skirt).

## 3. The kit

The kit is split into families: `construcao`, `formas`, `flora`, `rocha`, `humano`, `quadrupede`. Read only what
the asset needs: `pfe catalogo <family> ... --json` (for a plant, `pfe catalogo flora`) writes in `<acervo>/catalogo/`:

- `index.json`, the summary: every family with its pieces and what each is for, and the style's material list;
- `<family>.json`, the full pieces of the requested families: type (`prop`, `humanoide`, `quadrupede`), arguments
  (name, type, purpose, default; no default = required), variations with their arguments (the fastest way to see the
  units), the parts generated in the first variation (the ids that traits cite; `copa_00..copa_29` is a numbered
  range), and the anchors it leaves;
- one sheet per piece (`<piece>.png`: its variations, left to right).

With no family it writes all of them. Choose pieces by description and sheet. Only what is current exists: a piece
not in the catalogue does not exist.

## 4. The composition

A JSON `<id>.r<n>.json` (`<id>` in lowercase, `_` and digits). Fields:

| Field | What it is |
|---|---|
| `id`, `revision` | the asset and the revision (1 on the first) |
| `description`, `reference` | what it is, and the sheet |
| `tipo` | `prop` (static, on the root), `humanoide` or `quadrupede` (the model's rig) |
| `categoria` | the expected size (table below); the engine measures the height and refuses outside the range |
| `semente` | integer seed; each node's seed comes from it and the node id |
| `medidas` | names → expressions, used in arguments as `$name` |
| `nos` | the pieces, in order (see below) |
| `vistas` | static prop: `{"S": {}}` (2 or 4 cardinals only if requested); walkers: the 8 directions `S SW W NW N NE E SE` |
| `movimento` | prop: `["static"]` (sway `{"receita": "balanco", ...}` or spin `{"receita": "giro", ...}` if requested); human and quadruped: `["idle", "walk"]`; armed human, also `"attack"` (the sword strike, no loop) |
| `landmarks` | game points on the prop (`"sort_front": ["0", "0", "0"]`) |
| `tracos` | what must read in the sprite: `id`, `description`, `parts` (part ids), `verification` (`observable`: refused if no view shows a pixel of it) and optionally `reads_in_silhouette` (must touch the figure's edge) |

**Expressions:** numbers with a unit (`1.2m`, `30cm`, `8mm`, `3px`, `120%`, `15deg`), `$measure`, `+ - * /`, `min`,
`max`, `round` and parentheses. Size comes from real metres: the 1.65 m human is ~44 px on screen.

**A node:** `{"id", "peca", "args"}` and, if needed: `repete` (`{"sobre": "lados", "n": 2}` gives `$lado` −1 and 1;
`"linha"` gives `$i` and `$t`; `"anel"` gives `$cos` and `$sen`), `grupo` (the outline: parts of the same group are
not outlined against each other), `pilha` and `camada` (in the same stack, the node with the higher layer covers the
lower one it touches: a roof one layer above the wall covers its top where the eave comes down on screen; a piece's
inner faces sit between its layer and the next; for nothing to cover anything, use different stacks), `osso` (`raiz`;
with sway, `tronco` or `cadeia`; with spin, `giro`). An argument can cite an anchor left by an earlier node:
`"pontas": "galhos.pontas"`.

**Limits:** `description` and trait texts up to 400 characters, `reference` up to 2000, up to 64 nodes, and the sprite
up to 512 px a side (the canvas includes the ground shadow, on the right). Exceeding a limit is a refusal with the
measurement and a hint.

**Coordinates:** +X to the asset's left (screen right), +Y forward (towards the S camera), +Z up; the origin is the
asset's foot.

**The camera** is a single oblique 3/4: height shows at cos 45°, and ground and top at 0.6 (what is in front comes
down 0.6 px per px on screen); light comes from above and from the left, and the ground shadow falls to the right. The
contract is in `docs/coordenadas.md`.

**The human:** the first node is `corpo_humano`; clothes come after, one node per piece. The `espada` goes in the
right hand and gives the canvas 16 px more on top and on each side; with it, the `attack` clip (480 ms, 8 frames, no
loop) raises the blade over the shoulder and cuts forward. **The quadruped:** one `corpo_canino` node, with markings
and ears as arguments.

**A loose rock** is the `penedo`, not the `elipsoide` (which reads as an egg): a polyhedron drawn from the seed, with
faces, corners and tone by normal; `agudo` closes the tip, `inclina` tilts the top, `irregular` chips it, `musgo`
covers the top faces, `fendas` cracks the largest ones, and `material` is the family (`alvenaria`, granite; `palha`,
sandstone, with `tom` -1). Another seed gives another rock of the same kind: to vary the scene, vary the seed and the
shape, not only the size.

**A plant** has no single recipe. Choose the construction from the species sheet; in a set, use more than one:

| Construction | Nodes | What it gives |
|---|---|---|
| mass | `tronco_em_pe` + `copa` | the closed-crown broadleaf. `perfil`: 0 round, 1 teardrop (thin on top), -1 umbrella (upper half only). `tufos` and `tamanho`: a heavy crown (6 of 0.45) or a light one (14 of 0.22). `pende`: the curtain of thin hanging twigs around the crown (1 reaches the crown's bottom; 2 or more, with negative `perfil`, is the weeping tree) |
| open | `tronco_em_pe` + `galhos` with `sobe` + `copa_aberta` | visible branches and a cloud of leaves on each tip: the old tree, the sparse crown, the cloud-pruned crown |
| tiers | `tronco_em_pe` + `copa_conica` | the conifer with jagged skirts; `pontas`, `recorte` and `cai` give a full or a thin skirt |
| rosette on top | `tronco_em_pe` + `touceira` with `pe` at the trunk top, `largura` and `pena` | the palm (feathered), the sword leaf (smooth) |
| dead | `tronco_em_pe` + `galhos` | the leafless tree |
| bush | `copa` on the ground, no trunk | the shrub; with `salpico` on its `superficie`, flowers and fruit; a bush of two or three masses is several `copa` nodes with `desvio`, in the same `grupo` |
| clump | `touceira` | blades: thin, grass and reeds; with `largura` and `pena`, the fern; with `salpico` on the `pontas`, wild flowers and seed heads (a flower needs an almost straight blade, `cai` up to 0.1; an upright seed head, `alonga` 3) |

Foliage is one mass of light (bright on top and on the left) per `grupo`: foliage nodes in the same group brighten and
darken together, each lobe is a relief on the mass, and each lobe's edge is cut into leaves. `desvio` moves the crown
off the axis (the one-sided crown, the wind-beaten tree). Everything is drawn from the seed: another seed gives
another plant of the same species. **To vary the scene,** two plants of the same set must not come from the same
recipe with another seed and another size: vary the construction, the `perfil`, the crown proportion, the trunk
(`curva`, `inclinacao`, `raizes`, two trunks) and the foliage; within one species, the seed and `irregular`. The
critique (section 6) measures the silhouette against the siblings in the store and flags the lookalike. A plant is not
made of `elipsoide`, `poligono` or `fios`: the critique flags the egg, the smooth cone and the flat tone. A herb under
40 cm goes in the `objeto` category (`arbusto` starts at 0.25× the human).

A mass crown shows its top and covers the trunk from the front: the trunk left on screen is the crown centre height ×
0.71 minus √((half depth × 0.6)² + (half height × 0.71)²); to show more of it, raise the crown or reduce `fundo`. The
crown's shadow falls on the ground to the right and is part of the canvas. Take the trunk up to near the crown centre
(lobes recede from the edge: a trunk that stops at the crown's base leaves it in the air). Under a mass crown the
`galhos` barely show (they leave their tips for the crown to put a tuft on each) and are listed in `escondidas`: that
is expected. `galhos` leave from the vertical axis, not from a leaning trunk: keep `inclinacao` small when there are
branches. A trunk is not a cylinder: by default the foot flares at the ground and the stem thickens and thins; give it
what the species has (`curva` for a young trunk, `raizes` and `nos` for an old one, bark with upright grain,
`casca_sulcada` brown and `casca_cinzenta` grey, or `casca_anelada` with horizontal rings; `casca_clara` is smooth
and, on a thin trunk, reads as a pipe). Small bushes and crowns (under ~1.5 m wide) need few large lobes (5 or 6 of
0.45): with many small ones the relief disappears.

**Size by category** (in 1.65 m humans):

<!-- portes -->
| Category | Range | Typical |
|---|---|---|
| `arvore_grande` | 1.8× to 4.0× | ~2.5× (~4 m in game) |
| `arvore_pequena` | 1.0× to 2.0× | ~1.5× |
| `arbusto` | 0.25× to 1.0× | ~0.6× |
| `casa` | 1.3× to 3.0× | ~2× |
| `estrutura` | 0.3× to 2.5× | 0.3× to 2.5× |
| `objeto` | 0.1× to 1.5× | 0.1× to 1.5× |
| `prop_de_mao` | 0.03× to 0.6× | ~0.3× |
| `humano` | 0.6× to 1.25× | ~1× |
| `quadrupede` | 0.15× to 1.2× | ~0.5× |
<!-- /portes -->

**Examples made to the current standard** (read the one of the same type before composing; do not copy: the asset is
born from its own sheet): `tests/fixtures/exemplos/banco.r1.json` (single-view static), `arvore_folhosa.r1.json` (mass
crown tree), `arvore_aberta.r1.json` (visible-branch tree, with `copa_aberta`), `viajante.r1.json` (human, 8
directions) and `canino.r1.json` (quadruped, 8 directions).

## 5. The path

The asset store is `~/.pixel-forge/acervo` (or `--acervo`, or `PFE_ACERVO`). Save the composition in
`<acervo>/composicoes/`.

1. `pfe previa <composition> --json`: the rest pose of each view with the same refusals as the build, the sheet
   (`previas/<id>.r<n>.png`, real crop enlarged up to 4×) and the numbers: views, canvas, height, size, the `partes`
   ids (which traits cite), `escondidas` (per view, parts the view draws and no pixel shows; a crown's volumes are not
   listed: its far side is always hidden), each trait's pixels per view (`tracos`) and, for a plant, `critica` (the
   measurements and findings of section 6, without siblings). Read the numbers, then the sheet; adjust the composition
   and repeat. A hidden part that should show (the eye under the brim, the far hand) is a defect, and so is a
   `defeito` finding: do not go on with them.
2. `pfe radiografia <composition> --json`: the model enlarged up to 4× from geometry, front, profile and back in
   elevation (no game camera) and, on the bottom row, in the game camera (`radiografias/<id>.r<n>.png`). This is where
   shape is analysed: at game size a face is 5 px, and a shape defect hides in the reduction. For a human it returns
   the body `medidas`, each with the real-body range and what it means: one outside its range is a model (engine)
   defect, not a composition one; say so, do not hide it with clothes or pose.
3. `pfe conjunto <composition> ... --json`: the assets side by side on the ground, with the 1.65 m human as ruler.
4. `pfe checar <composition> --json`: every frame of the build checked (the walkers' clips), nothing written.
5. `pfe build <composition> --json`: the frames in the store; returns the `build`.
6. For a plant, `pfe critica <build> --json` and another agent's review (section 6): without a passing critique the
   package is refused (`CRITICA_PENDENTE`).
7. `pfe exportar <build> --json` and `pfe exportar <build> --verificar --json`: the game package (`pfe-jogo/1`, atlas
   and JSON) and its re-read against the build.
8. `pfe olhar <build> --json`: the sheet of every frame in the package and the numbers (one row per clip and
   direction, in the order of `clipes` and, within a clip, directions in alphabetical order: E, N, NE, NW, S, SE, SW,
   W).

Every refusal comes as `{"ok": false, "errors": [{"code", "message", "hint", "path"}]}`, with the path in the
composition: follow the hint and fix it. A `MOTOR` refusal is an engine defect, not yours: stop and report it.

## 6. The plant critique

A plant (tree, shrub, any asset with `copa` or `touceira`) only ships after being measured and reviewed by another
agent. `pfe critica <build> --json` (only the build path: the store is the build's) returns:

- `medidas` and `achados`: each finding has `codigo`, `gravidade`, `medida` and `dica`. A `defeito` (foliage that is
  smooth, mirrored or without a bright side; a silhouette equal to a sibling's) stops the critique from passing: fix
  the composition and go back to step 1 with `pfe atualizar`. An `aviso` (the vanished trunk, the loose piece) asks for
  the reviewer's eye. A defect you believe is measured wrong is an engine defect: stop and report it, do not work
  around it.
- `irmas`: the three compositions of the same category in the store (built or not) with the closest silhouette, and
  how close (0 to 1; from `parecida_a_partir_de` up it is a defect). A clump has no mass measurement: only its
  silhouette is compared.
- `prancha` (`criticas/<build>.png`): on top, the sprite and its silhouette; below, the siblings and their silhouettes.
- `perguntas` and `ficha`: what only the eye can answer.

Whoever answers the questions is not whoever composed. Give another agent (a subagent without your conversation) only
the sheet, the reference and the questions, without your explanation. Tell it what the sheet is (enlarged up to 4×;
sprite and silhouette on top, siblings below), the scale (the 1.65 m human is ~44 px), where the light comes from, and
to judge as the player who sees the sprite in the scene: a defect that is noticed fails; a detail of the reference
that does not fit in a few pixels only goes in the note. It looks at the image and answers each question with `ok` and
a note of what it saw. Save its answers in a file and register them:

```json
{"respostas": {"silhueta": {"ok": true, "nota": "wide low crown on a short trunk: reads as a garden tree"},
               "massa_de_luz": {"ok": false, "nota": "the right side is a dark blot with no relief"}}}
```

`pfe critica <build> --parecer <file.json> --por <who reviewed> --json` (every question, each note with 12 characters
or more). The `veredito` is `passa` with no measured defect and every answer good; otherwise it is `corrigir`, and
`a_corrigir` lists what is missing: change the composition, run `pfe atualizar` and redo the path (the new build needs
its own critique). The critique does not approve the art: that stays with the owner (section 8).

## 7. Completing and fixing

A revision is immutable: the build refuses (`IDENTIDADE`) the same revision with another drawing. So is a build: its
id carries the composition, the style, the engine version and the pixels, so the same id is always the same drawing; if
the engine changes a pixel, the same request gives another build, and the old package stays valid for the old build.
To complete or fix, edit the composition and run `pfe atualizar <composition> --json`: it becomes the next revision in
the store; follow the path with the file it returns.

## 8. Delivery

Deliver the package path (`exports/<build>/atlas.json`), the `olhar` sheet and the numbers; for a plant, also the
critique sheet, the siblings and who reviewed. The package ships as a preview, with the art pending: only the owner
reviews it (`pfe revisar <build> --veredito ... --nota ... --por ...`), and only an approved build ships with
`pfe exportar <build> --publicar`.
