# Ravaged

A choice-driven zombie survival game by **Samantha Hannah Wynne**. Explore an abandoned city, collect supplies, survive encounters, and choose how your story ends.

The terminal and browser editions run the **same Python engine**. There is no separate JavaScript rewrite of the game rules.

**[Play Ravaged online](https://samantha-hannah-wynne.github.io/Ravaged/)**

## Play in the terminal

Requires Python 3. No packages need to be installed.

```sh
python3 main.py
```

Enter a survivor name, then select numbered choices. Ctrl+C or the quit option ends the session. Progress is not saved between sessions.

## Play in a browser locally

From this directory:

```sh
python3 -m http.server 4174 --bind 127.0.0.1
```

Open <http://127.0.0.1:4174>. Use HTTP rather than opening `index.html` as a local file: the browser needs to fetch the Python source files.

The browser downloads the pinned Pyodide 0.27.7 runtime from jsDelivr, then runs `game.py`, `player.py`, and `zombie.py` locally. The first load requires internet access and can take a few seconds. Google Fonts also needs internet access; system fonts are used if unavailable. Runtime failures show a retry control.

Player names and game actions stay in browser memory. There are no accounts, analytics, server-side game APIs, or saved games.

## Rules

- Explore to discover routes, supplies, and encounters.
- A strike deals 20 damage. A surviving zombie retaliates for 10. Both combat choices retain the original game's damage values.
- Running costs 10 health and ends the current encounter.
- Rest restores up to 15 health. It does not silently spend or repeatedly reuse a medkit.
- A medkit restores up to 30 health and is consumed only when healing is needed.
- Ammo is spent only through the encounter's ammo action, allowing an escape.
- Keys open a medical room. The flashlight and map reveal additional routes and supplies.
- Reach the street with a flashlight and ammo after at least two scenes to unlock the final choice. An active encounter must be resolved first, and a dead player cannot escape.
- Invalid input never silently selects an ending.

## Run tests

```sh
python3 -m unittest discover -s tests -v
```

The suite covers inventory, healing, combat, contextual routes, both final choices, death precedence, invalid inputs, and terminal EOF handling.

## GitHub Pages

Publish this directory as the root of its own repository. Enable **Settings → Pages → Deploy from a branch**, then select `main` and `/ (root)`. `.nojekyll` keeps the static files available without a Jekyll build.

All game assets and Python source URLs are relative, so the site works under a repository URL such as `https://ACCOUNT.github.io/Ravaged/`. No secrets or deployment tokens belong in this repository.

## Files

- `game.py`: shared game state, choices, routes, and endings.
- `player.py`, `zombie.py`: character and inventory logic.
- `main.py`: terminal interface.
- `index.html`, `style.css`, `web.js`: responsive browser interface and Pyodide integration.
- `tests/`: Python regression tests.
