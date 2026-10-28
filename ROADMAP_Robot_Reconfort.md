# 🤖 HAI716 — Robot de Réconfort : Roadmap to the final result

> Python 3.9+ · standard library only · pair project (binôme) · Project 1 = one robot, Project 2 = several robots (reuses P1 code)

---

## 0. What I found in the starter repo

| File | What it is | Status |
|---|---|---|
| `reconfort_io.py` | Loads the 4 JSON files (only checks `format` + `version`), `normaliser()` (tokenizer), `Trace` class (writes the output) | ✅ done, you may edit it |
| `demo.py` | Loads everything, prints a summary, fails every request on purpose | skeleton to replace |
| `donnees/dictionnaire.json` | 144 entries / **250 word forms** → (emotion, intensity) | data |
| `donnees/armoire_standard.json` | 24 slots. **Whole `surprise` column is empty**, plus `[2,7]` | data |
| `cartes/appartement_01..05.json` + `scenario_01..05.json` | 5 maps (9×13 up to 13×21, 2 to 4 residents) | data |
| `rendu.json`, `MODELE_README.md` | Templates for the submission | to fill |

### ⚠️ Things the starter does NOT give you (and the statement doesn't shout about)

1. **There is no simulator.** `grille` is "reserved for the simulator", but nobody provides one. *You* must write the world (`simulateur.py`) that answers perceptions and reveals cabinet contents. The agent talks to it only through a narrow interface.
2. **All the validation of section 5.6 is yours** (22 broken hidden files, 2 points). The loader checks almost nothing.
3. `demo.py`'s docstring shows 3 arguments but the code needs **4** (carte, scénario, données, trace). The 4-argument version is the real contract.
4. `Trace` only *records*: it never checks that your steps are legal. You need your own checker (Phase 8).

---

## 1. Purpose of the project (one paragraph)

A service robot in a residence receives short messages from residents. For each one it must **(1)** go next to the dictionary and `CONSULTER` to learn the emotion + intensity, **(2)** go next to the cabinet and move a *selector* slot by slot (`CHERCHER`) until it finds the right comfort object, `PRENDRE` it, **(3)** walk to the resident and `DONNER`. The robot is blind: it sees only its 4 adjacent cells, so it builds a **mental map** and re-plans. Grading replays your **trace** against reality, so every move, perception and slot content you log must be true.

---

## 2. Target architecture

The statement grades "perception / memory / decision / action clearly separated" (3 pts) and Project 2 reuses everything. Design for that now.

```
archive root/
├── agent.py                  # entry point: args → validate → build world → run → write trace
├── reconfort_io.py           # provided (lightly extended)
├── validation.py             # all section 5.6 checks (raises ErreurFichier)
├── rendu.json  README.md  rapport.pdf  demo.mp4
├── robot/
│   ├── geometrie.py          # directions N/S/E/O, deltas, neighbours
│   ├── roue.py               # Plutchik wheel: distance, candidate list (pure functions)
│   ├── lecture_emotion.py    # dictionary lookup (pure function)
│   ├── selecteur.py          # cabinet selector: cyclic columns, moves, route
│   ├── chemin.py             # BFS (deque), written by hand
│   ├── memoire.py            # mental map + cabinet memory
│   ├── perception.py         # what the robot receives each tick
│   ├── decision.py           # picks the next action (state machine)
│   └── action.py             # executes + logs an action
├── monde/
│   └── simulateur.py         # ONLY file allowed to read `grille` and `objet`
├── outils/
│   ├── visualiser.py         # replays a trace in the terminal (for the video)
│   └── verifier_trace.py     # your own "grader" replay
├── tests/                    # unittest
├── cartes_perso/             # maps/scenarios you build yourselves
└── .git
```

**The four-box loop (every tick):**

```
Simulateur ──perception──▶ Mémoire (update map / cabinet)
                              │
                         Décision (choose 1 action)
                              │
Simulateur ◀──action────── Action (execute + Trace.ajouter_pas)
```

**Rules that keep it clean:**
- `decision.py` never touches the simulator or the trace; it reads memory and returns an action.
- Only `simulateur.py` and `validation.py` read `grille`/`objet`. The agent gets a **"connaissances initiales"** object: dimensions, start position, armoire/dictionnaire/residents positions, cabinet *layout* labels, never walls or objects.
- No global state; one `Robot` object holds its own memory (so Project 2 can instantiate N of them).
- No function over ~50 lines; the statement explicitly punishes a 300-line monolith.

---

## 3. Tools

| Need | Tool | Why |
|---|---|---|
| Language | Python 3.9+ | Statement + starter. Avoid `match` and runtime `X \| Y` types to stay 3.9-compatible |
| Queue for BFS | `collections.deque` | `list.pop(0)` is O(n); the statement warns about it |
| JSON / paths | `json`, `pathlib` | Allowed |
| Tests | `unittest` | stdlib. Run: `python -m unittest discover -s tests` |
| Data structures | `dataclasses`, `enum` | Clear states and actions |
| Forbidden | `networkx`, `scipy.sparse.csgraph`, `igraph` | Shortest path must be hand-written |
| Version control | Git, small commits | History is graded (1 pt): real, gradual, readable |
| Video | any screen recorder (OBS, QuickTime, Game Bar, `asciinema`) | 1 min 30, no voice, terminal grid is enough |
| Report | any editor → PDF | 3 pages max |

---

## 4. Phase-by-phase plan

Each phase ends with working code, tests, and a commit. Order follows dependencies, not difficulty.

### Phase 1 — Set up the repo and understand the base
**Purpose:** a clean start and a shared understanding (both members will be questioned on `reconfort_io.py` at the defense).
- Create *your own* repo (don't work in the teachers' one), copy `base_fournie/`, add `.gitignore` (`__pycache__/`, `sorties/`).
- Run the demo: `python demo.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json`.
- Read `reconfort_io.py` together; each person explains `_lire_json`, `normaliser`, `Trace` to the other.
- **Commit:** "Initial import of base_fournie".

### Phase 2 — Pure logic modules (no robot yet, easy to test)
**Purpose:** the deterministic rules; they are what makes two correct teams produce the same deliveries.

1. **`geometrie.py`**: `DELTAS = {"N":(-1,0),"S":(1,0),"E":(0,1),"O":(0,-1)}`, `voisins(pos)`.
2. **`lecture_emotion.py`** (section 6.1): normalise → loop over words left to right → first word found in a `forme → (emotion, intensite)` dict wins → else `None` (`emotion indeterminee`). Build that dict once from the file; the word forms are already normalised.
3. **`roue.py`** (section 6.2 + annexe A):
   - Emotion order = the `emotions` field of the file (never reorder).
   - `distance(e1, e2) = min(k, 8-k)` with `k = (i2 - i1) % 8`.
   - `candidats(e, i)` → exactly **15** (emotion, intensity) pairs (3 same-emotion + 6 at distance 1 + 6 at distance 2), sorted by key `(distance, |Δintensity|, intensity lowest first, clockwise before counter-clockwise)`. Clockwise at distance d means index `+d`.
   - Label each candidate with its `repli`: `aucun` (the exact slot), `intensite` (same emotion), `voisine_1`, `voisine_2`.
   - ✅ I verified this ordering against annexe C.5 (surprise/forte → `[2,3] [1,3] [0,3] [2,4] [2,2] …`).
4. **`selecteur.py`** (annexe B.7 / C): position `(ligne, colonne)`, `N`/`S` illegal at rows 0/2, `E`/`O` wrap mod 8. `route(depart, arrivee)` with `a = (c'-c) % 8`; go `E` if `a <= 8-a`, else `O`. Allow vertical-first or horizontal-first (same cost).

**Tests (write them now):** items 3, 4, 5 of section 8 of the statement. Include `[1,0] → [2,6]` costing 3 moves (the trap example).

### Phase 3 — Path planning (BFS) and mental map
**Purpose:** the heart of the navigation.

1. **`chemin.py`**: BFS with a `deque`, a predecessor dict (it doubles as "visited"), multi-goal (`arrivees` is a set), returns the path or `None`. Follow the pseudo-code of annexe B.4.
2. **`memoire.py` mental map:**
   - A dict `{(l,c): "libre"|"mur"|"armoire"|"dictionnaire"|"resident"}`; **unknown = absent = assumed free** (optimistic hypothesis, annexe B.5).
   - Pre-fill with what the robot legitimately knows at start: armoire, dictionnaire and residents are **non-traversable** known cells. Out-of-grid cells count as walls.
   - `mettre_a_jour(position, perception)` writes the 4 neighbours and the current cell as `libre`.
   - `est_traversable(cell)`: known `mur/armoire/dictionnaire/resident` → False, else True.
3. **Targets are cells, not objects:** the goal set for "go to the cabinet / dictionary / resident X" = the **traversable cells orthogonally adjacent** to that object.
4. **Why a failed BFS is a proof (annexe B.6):** the mental map has *at least* as many free cells as reality. If no path exists even there, none exists in reality → `resident inaccessible`.

**Tests:** items 1, 2, 7 of section 8: hand-written grid with known length (use annexe B.3: path length **7**), a wall discovered en route changing the path, a walled-in resident on a tiny grid.

### Phase 4 — The simulator (`monde/simulateur.py`)
**Purpose:** the "reality" the robot interacts with. This is the *only* code that reads `grille` and `objet`.

- `percevoir()` → `{"N": "libre"|"mur"|"armoire"|"dictionnaire"|"resident", …}` for the 4 neighbours of the robot (the `R` cell counts as `libre`).
- `contenu_casier()` → object (or `None`) of the current selector slot, **only if the robot is adjacent to the cabinet**, else `None`.
- `appliquer(action, argument)` → checks legality (target cell free, adjacency to the cabinet / dictionary / resident, selector bounds, carrying at most one object) and updates the state. An illegal action raises an error in your tests so you catch bugs before the grader does.
- Keep the interface generic (robot id parameter) so Project 2 can add several robots.

### Phase 5 — The agent (perception / memory / decision / action)
**Purpose:** the actual robot, as a small state machine per request.

States for one request (section 4 of the statement):
`ALLER_DICTIONNAIRE → CONSULTER → (échec si inconnu) → ALLER_ARMOIRE → FOUILLER → PRENDRE → ALLER_RESIDENT → DONNER → fin`

**Per tick:**
1. **Perception:** get the 4 neighbours (+ slot content if in front of the cabinet).
2. **Memory:** update the mental map; if in front of the cabinet, record `casiers_vus[selector] = object or None` (**even the starting slot counts as seen the first time the robot is in front of the cabinet**).
3. **Decision:**
   - Moving to a target: BFS on the mental map from the current cell, take the **first step only**, re-plan next tick (simple and correct, the cost goes in the report).
   - BFS finds nothing for the resident → deliver failure `resident inaccessible`.
4. **Action:** execute through the simulator, then `trace.ajouter_pas(...)` with position/slot **before** the action and the perception made **from that position**.

**Cabinet search logic (the subtle part):**

```
candidats = roue.candidats(e, i)            # ordered list of 15
loop:
    first = first candidate whose slot is not known to be empty
    if none left                    → fail "armoire vide"
    if first has been seen (garni)  → move selector onto it, PRENDRE, done
    else                            → move selector toward it (CHERCHER step by step)
                                      every slot crossed is recorded as seen
```

Rules that matter:
- You may only skip a higher-priority slot if you **actually saw it empty** (section 3.3). Announcing a repli without having been in front of every higher slot = a **zeroed** functional score.
- Seeing a garni slot en route does **not** let you take it if a higher-priority candidate is still unseen/garni. The order always wins.
- The robot must stay **adjacent to the cabinet** during all `CHERCHER` moves.
- Cache validity: in Project 1 taking an object doesn't deplete the slot (stock is a Project 2 *extension*), so `casiers_vus` can persist across requests. If you do the stock extension, invalidate the cache.
- Route choice is free. Baseline = vertical first. Optimisation (later, optional): pick the route that crosses the next unseen candidates.

**Failures never stop the scenario:** log the delivery with `succes=False` + `motif_echec` and move on:
- `emotion indeterminee` → right after `CONSULTER`, no trip to the cabinet.
- `armoire vide` → all 15 candidates seen empty.
- `resident inaccessible` → BFS proof.

**Safety net:** a global step cap (a few times `hauteur × largeur`, per request) so a bug can never cause an infinite loop. The statement forbids infinite loops on bad input.

### Phase 6 — Validation of input files (2 pts, 22 hidden broken files)
**Purpose:** each broken file must give **non-zero exit code + readable message on stderr + no trace file written**.

Create `validation.py`, call it **before** any simulation, and write the trace **only at the very end**.

| Category (section 5.6) | Check |
|---|---|
| File problems | absent, unreadable, not UTF-8, invalid JSON (already in `_lire_json`) |
| Header | `format` / `version` (already done) |
| Fields | each required field present and of the right type, for all 4 files |
| Grid | rectangular, matches `dimensions` |
| Positions | inside the grid |
| Symbols | robot start on `R`, armoire on `A`, dictionnaire on `D`, each resident on `P` |
| Residents | unique ids |
| Scenario | `carte` equals the map `nom`; every `resident` exists on the map; the `armoire` file exists |
| Cabinet | slot inside 3×8, no duplicate slot, `emotion`/`intensite` labels consistent with `ligne`/`colonne`, `casier_depart` inside |
| Dictionary | unknown emotion/intensity; same word in two entries |

`agent.py` skeleton: wrong argument count → usage message + exit 2; `ErreurFichier` → `print(..., file=sys.stderr)` + exit 1; **never a Python traceback**. Build one **broken file per category** (≈22) in `tests/fichiers_casses/` and a test that runs `agent.py` as a subprocess on each.

### Phase 7 — Tests (3 pts)
Required by section 8; each must be able to fail (a test that can't fail doesn't count, and generated-but-unread tests are spotted):

1. planning on a hand-written grid (known length)
2. re-planning after a wall is discovered
3. dictionary: one message per emotion, first-word-wins, no recognised word
4. selector moves incl. wrap column 7 ↔ 0
5. fallback: exact slot full / empty → intensity repli / whole column empty → neighbour / nothing within distance 2
6. validation: one broken file per category
7. walled-in resident on a tiny grid

Plus integration tests: run the 5 provided scenarios and pass the traces through `verifier_trace.py`.

### Phase 8 — Your own grader (`outils/verifier_trace.py`)
**Purpose:** the real grader replays the trace; you can't see it, so imitate it. This is the best protection against the "perception falsified / move illegal / repli without search" penalties.

Check, step by step, on the trace + the real map/cabinet:
- `t` starts at 0 and increments; `position`/`casier` before the action are consistent with the previous step's result.
- Every `AVANCER` target is free; every `CHERCHER` stays in bounds; adjacency for `CONSULTER/CHERCHER/PRENDRE/DONNER`.
- Logged `perception` equals reality; logged `contenu_casier` equals the real content when in front of the cabinet, else `null`.
- `PRENDRE` only on a non-empty slot and while carrying nothing; `DONNER` to the right resident with the right object.
- For each delivery: the chosen slot is the **first non-empty candidate** in the rule order; every higher-priority candidate appears as *seen* in the trace before the `PRENDRE`; `repli` label is right.
- Summary numbers match.

### Phase 9 — Your own maps (hidden test set)
The hidden set includes a **bigger apartment, a cabinet with an entire empty column, an inaccessible resident**, plus the broken files. Build in `cartes_perso/`:
- a large map (e.g. 25×40) with long corridors and dead-ends,
- a map with a walled-in resident,
- a cabinet where a full column and several slots are empty (also empty row, empty neighbours → "armoire vide"),
- scenarios with unknown words, repeated residents, and a `[2,7]`/`[0,0]` wrap case,
- a map where a resident is *adjacent to a wall pocket* (BFS must prove unreachability without looping).

### Phase 10 — Terminal display and video (1 pt)
- `outils/visualiser.py` reads a trace + map and redraws the grid each step (ANSI clear + `time.sleep`), showing robot position, the discovered walls, the selector position and the object carried. Doing it as a separate tool keeps the 4-argument contract untouched.
- Record 1 min 30 max, no voice or editing. **Frame the moment the robot hits an unexpected wall and re-routes** (appartement_01: east along row 6 → wall at `[6,7]` → back up via row 2).
- Declare it in `rendu.json` (`"video": "demo.mp4"` or an accessible URL).

### Phase 11 — Report (2 pts, 3 pages max)
Four points only:
1. **Architecture:** schema + why the perception/memory/decision/action boundaries are where they are.
2. **Replanning strategy:** full re-plan each tick (BFS is O(cells), instant on 15×21) vs. repairing the plan; cost and trade-off.
3. **Critique of the fallback rule:** answering sadness with an object stored under "disgust" can be inappropriate. Propose a better rule (e.g. rank by *valence/polarity* of the emotion instead of pure wheel distance, or restrict to comforting/neutral neighbours, or add a per-object "comfort" score) and say what must change in the files (new field per slot such as `valence`/`score`, a change in `armoire.json` and the dictionary).
4. **Three real failures of your robot**, with cause analysis. Ideas from the statement and from this design: re-crossing already-known-empty slots, a cabinet route that ignores the next candidates, full re-planning wasted per tick, wandering to prove an inaccessible resident. An "everything works" report is read as "didn't look".

### Phase 12 — Packaging and defense
- `rendu.json`: real names, `"commande": ["python", "agent.py"]`, `"video"`.
- README from `MODELE_README.md`: how to run, how to test, what works, **what doesn't (be honest, it counts in your favour)**.
- Zip `NOM1_NOM2.zip` with `.git` included.
- Test from a **fresh clone in another folder**, and with absolute paths for the 4 arguments (no hard-coded paths).
- **Defense (20 min):** random code portion, **both** members must explain any part, including the other's; "that's my partner's part" = 0 for that portion. Do cross-reviews: each of you explains the other's modules aloud before the defense.

---

## 5. Suggested pair split (with mandatory cross-review)

| Person A | Person B |
|---|---|
| Phase 2: `roue`, `lecture_emotion`, `selecteur` | Phase 3: `chemin`, `memoire` |
| Phase 4: simulator | Phase 6: validation |
| Phase 5: cabinet search logic | Phase 5: movement/state machine |
| Phase 8: verifier | Phase 10: visualiser + video |
| Review B's code | Review A's code |

Merge through short branches/PRs so the Git history shows real, gradual work (not one giant commit at the end).

---

## 6. Pitfalls checklist

- [ ] Perception is read **before** deciding; the robot never walks into an unseen wall (it sees it first). "Bumping into a wall" in the video = discovering it on arrival, then re-routing.
- [ ] `position` and `casier` in a step are the values **before** the action.
- [ ] `contenu_casier` is logged on **every** step where the robot is adjacent to the cabinet, `null` otherwise.
- [ ] The `R` start cell is free; map border is always wall; no diagonals.
- [ ] Residents, armoire and dictionnaire are **obstacles** for BFS (goal = a free neighbour cell).
- [ ] Rows of the cabinet don't wrap; columns do. At `a == 4` both directions cost 4 (formula picks `E`).
- [ ] Candidates beyond distance 2 are **never** used.
- [ ] You must have *seen* a slot empty before skipping it. Passing in front of a garni lower-priority slot doesn't allow taking it.
- [ ] Selector position persists across requests; the robot keeps its mental map across requests too.
- [ ] Trace written only on success path; nothing written on invalid input.
- [ ] No reading of `grille`/`objet` in agent code. Isolate it in `simulateur.py` / `validation.py`.
- [ ] Python 3.9 compatibility, zero third-party packages.

---

## 7. Open questions to ask your teacher (don't guess)

1. **Resident unreachable *after* `PRENDRE`.** The order is dictionary → cabinet → resident, and the robot only learns the resident is unreachable by exploring. But there is no "drop" action, and `PRENDRE` requires carrying nothing. If the robot already holds an object when it fails, how should the next request work? Options: (a) explore toward the resident *before* going to the cabinet, (b) `DONNER` to another resident being allowed, (c) the failing request simply drops it conceptually. This directly affects the hidden "inaccessible resident" test.
2. **How is the "no `grille` / no `objet`" rule checked automatically?** Replay-based (perceptions/contents) or static text search of source files? That decides how strictly to isolate `simulateur.py`.
3. **Is the starting selector slot `casier_depart` counted as "seen"** as soon as the robot first stands in front of the cabinet?
4. **Does `PRENDRE` deplete a slot in Project 1?** (The stock extension in 12.4 suggests no.)

---

## 8. Project 2 preview (design choices to make *now*)

Same apartment, 2–4 robots, simultaneous requests. To avoid rewriting:
- Keep `Robot` as a self-contained class (own mental map, own selector knowledge), parameterised by an id.
- Make the simulator accept `percevoir(robot_id)` / `appliquer(robot_id, action)`.
- Keep the **cost estimation** (BFS distance on the robot's own mental map) as a separate function: it becomes the auction bid.
- Another robot seen in a neighbour cell must be a **temporary obstacle**: don't write it into the permanent mental map (use a per-tick overlay).
- Cabinet/dictionary reservations and deadlock-freedom (priority by id, timeout + back-off) need a written argument that they terminate.
- Plan the **1 robot vs N robots comparison** (total steps, makespan) on the same scenarios; it is worth 4 of the P2 points.

---

## 9. Milestone summary

| # | Milestone | Done when |
|---|---|---|
| M1 | Repo + base understood | demo runs, first commit |
| M2 | Pure rules | dictionary / wheel / selector tests green |
| M3 | BFS + mental map | planning + replanning tests green |
| M4 | Simulator + agent | scenario_01 delivers all 4 requests, trace passes your checker |
| M5 | All 5 provided scenarios | checker green on all 5 |
| M6 | Validation | one broken file per category, exit ≠ 0, no trace |
| M7 | Hidden-set readiness | custom large map, empty-column cabinet, inaccessible resident pass |
| M8 | Deliverables | video, report, README, `rendu.json`, zip from a fresh clone |
| M9 | Defense prep | each member explains every module |
