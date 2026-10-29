import './style.css';
import { WorldView } from './world-view.js';
import { ExplorationAgent } from './agent.js';

const app = document.querySelector('#app');
app.innerHTML = `
  <main class="layout">
    <header class="topbar">
      <div><div class="eyebrow">AUTONOMOUS EXPLORATION · PROTOTYPE 01</div><h1>Agent World</h1></div>
      <div class="controls"><span class="live"><i></i> WORLD LIVE</span><button id="pause">Pause</button><button id="reset" class="quiet">Reset</button></div>
    </header>
    <section class="world-panel">
      <div id="world" aria-label="3D world visualization"></div>
      <div class="world-caption"><span>01 / THE STUDY</span><span>GRAVITY 9.8 m/s²&nbsp; · &nbsp;24-HOUR LIGHT CYCLE</span></div>
      <div class="agent-badge"><span class="avatar">●</span><div><strong>Wanderer</strong><small id="agent-status">observing the world</small></div></div>
    </section>
    <aside class="side-panel">
      <section><div class="section-heading"><span>INNER STATE</span><span class="pulse"></span></div><div class="current-goal"><small>CURRENT CURIOSITY</small><div id="goal">Taking in the surroundings</div></div></section>
      <section><div class="section-heading">FIELD NOTES <span id="note-count">00</span></div><div id="notes" class="notes"></div></section>
      <section><div class="section-heading">RECENT EVENTS</div><div id="events" class="events"></div></section>
      <footer>LLM CONNECTOR: <b>SIMULATED BRAIN</b><br/>No external model is connected yet.</footer>
    </aside>
    <div class="bottom-bar"><span><b>SIM TIME</b> <span id="clock">06:00</span></span><span>AGENT: <b>SELF-DIRECTED</b></span><span>OBJECTS: <b id="object-count">04</b></span><span class="hint">Drag to orbit · Scroll to zoom</span></div>
  </main>`;

const ui = {
  status: document.querySelector('#agent-status'), goal: document.querySelector('#goal'),
  notes: document.querySelector('#notes'), noteCount: document.querySelector('#note-count'),
  events: document.querySelector('#events'), clock: document.querySelector('#clock'),
  pause: document.querySelector('#pause')
};

const view = new WorldView(document.querySelector('#world'));
const agent = new ExplorationAgent({ onUpdate: render });
let running = true;
let previous = performance.now();

function render(state) {
  ui.status.textContent = state.status;
  ui.goal.textContent = state.goal;
  ui.noteCount.textContent = String(state.notes.length).padStart(2, '0');
  ui.notes.innerHTML = state.notes.slice().reverse().map(n => `<article class="note"><time>${n.time}</time><p>${escapeHtml(n.text)}</p></article>`).join('');
  ui.events.innerHTML = state.events.slice(0, 5).map(e => `<div class="event"><time>${e.time}</time><span>${escapeHtml(e.text)}</span></div>`).join('');
  ui.clock.textContent = formatClock(state.worldTime);
  view.setAgentPose(state.agent);
  view.setObjects(state.objects);
}

function escapeHtml(text) { return text.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function formatClock(seconds) { const minutes = Math.floor((seconds / 120) * 24 * 60) % (24 * 60); return `${String(Math.floor(minutes / 60)).padStart(2,'0')}:${String(minutes % 60).padStart(2,'0')}`; }

function frame(now) {
  requestAnimationFrame(frame);
  const dt = Math.min((now - previous) / 1000, 0.05);
  previous = now;
  if (running) agent.update(dt);
  view.update(dt, agent.worldTime);
}
requestAnimationFrame(frame);

ui.pause.addEventListener('click', () => {
  running = !running;
  ui.pause.textContent = running ? 'Pause' : 'Resume';
  document.querySelector('.live').innerHTML = running ? '<i></i> WORLD LIVE' : '<i class="paused"></i> WORLD PAUSED';
});
document.querySelector('#reset').addEventListener('click', () => { agent.reset(); running = true; ui.pause.textContent = 'Pause'; });
