const $ = (selector) => document.querySelector(selector);
let beginGame;
let chooseAction;
let currentState;

async function loadEngine() {
  $('#start-button').disabled = true;
  $('#load-error').hidden = true;
  $('#runtime-status').textContent = 'Downloading the Python runtime…';
  try {
    const { loadPyodide } = await import('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs');
    const python = await loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/' });
    $('#runtime-status').textContent = 'Loading the streets, supplies, and stories…';
    await Promise.all(['player.py', 'zombie.py', 'game.py'].map(async (filename) => {
      const response = await fetch(new URL(filename, import.meta.url));
      if (!response.ok) throw new Error(`${filename} could not be loaded (HTTP ${response.status}).`);
      python.FS.writeFile(filename, await response.text());
    }));
    python.runPython(`
import json
from game import Game

def begin_game(name):
    global current_game
    current_game = Game(name)
    return json.dumps(current_game.snapshot())

def choose_action(action):
    return json.dumps(current_game.choose(action))
`);
    beginGame = python.globals.get('begin_game');
    chooseAction = python.globals.get('choose_action');
    $('#start-button').disabled = false;
    $('#runtime-status').textContent = 'The city is waiting. Your story is ready.';
  } catch (error) {
    console.error('Ravaged engine failed to load:', error);
    $('#runtime-status').textContent = 'The game could not start.';
    $('#error-message').textContent = 'The Python runtime or game files could not be downloaded. Check your internet connection and whether your browser allows cdn.jsdelivr.net, then try again.';
    $('#load-error').hidden = false;
  }
}

function render(state, focus = true) {
  currentState = state;
  $('#survivor-name').textContent = state.name;
  $('#health-value').textContent = state.health;
  $('#health-bar').value = state.health;
  $('#health-description').textContent = state.health === 0 ? 'The city has claimed you.' : state.health <= 30 ? 'You need to recover. Soon.' : 'Still standing.';
  $('#location').textContent = state.location;
  $('#enemy-status').hidden = state.zombie_health === null;
  $('#enemy-status').textContent = state.zombie_health === null ? '' : `Zombie health: ${state.zombie_health} / 60`;
  $('#scene-label').textContent = state.outcome ? 'THE LAST PAGE' : state.scene ? `SCENE ${String(state.scene).padStart(2, '0')} / ${state.location.toUpperCase()}` : 'PROLOGUE / THE CITY';
  const inventory = $('#inventory');
  inventory.replaceChildren();
  state.inventory.forEach((item) => {
    const li = document.createElement('li');
    const name = document.createElement('strong');
    name.textContent = item.name;
    const description = document.createElement('span');
    description.textContent = item.description;
    li.append(name, description);
    inventory.append(li);
  });
  $('#empty-inventory').hidden = state.inventory.length > 0;
  const narrative = $('#narrative');
  narrative.replaceChildren();
  state.messages.forEach((message) => {
    const paragraph = document.createElement('p');
    paragraph.textContent = message;
    narrative.append(paragraph);
  });
  $('#prompt').textContent = state.prompt;
  const choices = $('#choices');
  choices.replaceChildren();
  state.options.forEach((option, index) => {
    const button = document.createElement('button');
    button.className = 'choice';
    button.dataset.action = option.id;
    const number = document.createElement('span');
    number.className = 'choice-number';
    number.textContent = String(index + 1).padStart(2, '0');
    number.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span');
    label.textContent = option.label;
    const arrow = document.createElement('span');
    arrow.className = 'choice-arrow';
    arrow.textContent = '↗';
    arrow.setAttribute('aria-hidden', 'true');
    button.append(number, label, arrow);
    button.addEventListener('click', () => {
      try {
        $('#game-error').hidden = true;
        render(JSON.parse(chooseAction(option.id)));
      } catch (error) {
        console.error('Ravaged could not complete the action:', error);
        $('#game-error').textContent = 'That action could not be completed. Try again, or start a new story.';
        $('#game-error').hidden = false;
      }
    });
    choices.append(button);
  });
  $('#ending-panel').hidden = !state.outcome;
  $('#ending-label').textContent = { survived: 'YOU SURVIVED THE NIGHT.', lost: 'NOT EVERY STORY ENDS AT DAWN.', quit: 'ANOTHER NIGHT. ANOTHER CHANCE.' }[state.outcome] || '';
  if (focus) {
    const target = state.outcome ? $('#play-again') : $('#prompt');
    target.focus({ preventScroll: true });
    const story = $('.story-panel').getBoundingClientRect();
    if (story.top < 0 || story.top > window.innerHeight / 2) {
      $('.story-panel').scrollIntoView({ behavior: 'instant', block: 'start' });
    }
  }
}

$('#start-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const name = $('#player-name').value.trim();
  if (!name) {
    $('#player-name').setCustomValidity('Enter a name for your survivor.');
    $('#player-name').reportValidity();
    return;
  }
  try {
    const state = JSON.parse(beginGame(name));
    $('#intro').hidden = true;
    $('#game-screen').hidden = false;
    render(state);
  } catch (error) {
    console.error('Ravaged could not start a story:', error);
    $('#runtime-status').textContent = 'Your story could not start. Please reload the page and try again.';
  }
});
$('#player-name').addEventListener('input', () => $('#player-name').setCustomValidity(''));
$('#retry-button').addEventListener('click', loadEngine);

const helpDialog = $('#help-dialog');
$('#help-button').addEventListener('click', () => helpDialog.showModal());
$('#close-help').addEventListener('click', () => helpDialog.close());
const restartDialog = $('#restart-dialog');
function reset() {
  currentState = undefined;
  $('#game-screen').hidden = true;
  $('#intro').hidden = false;
  $('#game-error').hidden = true;
  $('#player-name').focus();
  $('#intro').scrollIntoView({ behavior: 'instant' });
}
$('#restart-button').addEventListener('click', () => {
  if (currentState?.outcome) reset();
  else restartDialog.showModal();
});
$('#cancel-restart').addEventListener('click', () => restartDialog.close());
$('#confirm-restart').addEventListener('click', () => {
  restartDialog.close();
  reset();
});
$('#play-again').addEventListener('click', reset);
loadEngine();
