// Replace CuriosityBrain with an LLM-backed implementation behind this interface.
// LLM calls should be asynchronous and return high-level intentions, never per-frame controls.
const seedNotes = [
  { time: '06:00', text: 'I have just become aware of a quiet room and several objects.' }
];

export class ExplorationAgent {
  constructor({ onUpdate }) { this.onUpdate = onUpdate; this.reset(); }

  reset() {
    this.worldTime = 0;
    this.agent = { x: 0, z: 1.5, heading: 0 };
    this.objects = [
      { id: 'sphere', name: 'blue sphere', type: 'sphere', x: -2.2, z: -1.1, y: 0.42, color: '#77aee8', radius: .42, vx: 0, vz: 0 },
      { id: 'box', name: 'wooden box', type: 'box', x: 1.8, z: -1.2, y: .48, color: '#c18b5b', radius: .48, vx: 0, vz: 0 },
      { id: 'cylinder', name: 'green cylinder', type: 'cylinder', x: 2.7, z: 1.7, y: .5, color: '#78b89a', radius: .42, vx: 0, vz: 0 },
      { id: 'orb', name: 'golden orb', type: 'sphere', x: -2.8, z: 2, y: .36, color: '#e7be69', radius: .36, vx: 0, vz: 0 }
    ];
    this.notes = [...seedNotes];
    this.events = [];
    this.goal = 'Taking in the surroundings';
    this.status = 'observing the world';
    this.target = null;
    this.thinkTimer = 2.5;
    this.noteTimer = 0;
    this.emit();
  }

  update(dt) {
    this.worldTime += dt;
    this.thinkTimer -= dt;
    this.noteTimer += dt;
    if (this.thinkTimer <= 0) this.chooseGoal();
    this.moveAgent(dt);
    this.updatePhysics(dt);
    this.emit();
  }

  chooseGoal() {
    this.thinkTimer = 8 + Math.random() * 5;
    const object = this.objects[Math.floor(Math.random() * this.objects.length)];
    const ideas = [
      [`I wonder what happens if I approach the ${object.name}.`, `Approach the ${object.name}`, 'approach'],
      [`I want to learn whether the ${object.name} moves when touched.`, `Test the ${object.name}`, 'touch'],
      [`I should compare the ${object.name} with the other objects.`, `Look closely at the ${object.name}`, 'inspect']
    ];
    const [thought, goal, action] = ideas[Math.floor(Math.random() * ideas.length)];
    this.goal = goal;
    this.status = `curious about the ${object.name}`;
    this.target = { object, action };
    this.addEvent(`Formed a new curiosity: “${goal}.”`);
    if (Math.random() > .45) this.addNote(thought);
  }

  moveAgent(dt) {
    if (!this.target) return;
    const { object } = this.target;
    const dx = object.x - this.agent.x, dz = object.z - this.agent.z;
    const distance = Math.hypot(dx, dz);
    if (distance < 1.1) {
      this.agent.heading = Math.atan2(dx, dz);
      this.status = `exploring the ${object.name}`;
      this.completeCuriosity(object);
      return;
    }
    this.agent.heading = Math.atan2(dx, dz);
    const speed = 1.05;
    this.agent.x += dx / distance * speed * dt;
    this.agent.z += dz / distance * speed * dt;
  }

  completeCuriosity(object) {
    if (this.target.action === 'touch' && this.noteTimer > 1.5) {
      const dx = object.x - this.agent.x, dz = object.z - this.agent.z, d = Math.max(.01, Math.hypot(dx,dz));
      object.vx += dx / d * 1.25; object.vz += dz / d * 1.25;
      this.addEvent(`Touched the ${object.name}; it began to move.`);
      this.addNote(`The ${object.name} moves when I touch it.`);
      this.noteTimer = 0;
    } else if (this.target.action === 'inspect' && this.noteTimer > 1.5) {
      this.addNote(`The ${object.name} is ${Math.hypot(object.x-this.agent.x, object.z-this.agent.z).toFixed(1)} m away. Its color is ${object.color}.`);
      this.addEvent(`Observed the ${object.name} up close.`);
      this.noteTimer = 0;
    }
    this.target = null;
    this.status = 'reflecting on what happened';
    this.goal = 'Considering what to explore next';
    this.thinkTimer = 3;
  }

  updatePhysics(dt) {
    // Simple horizontal damping and room bounds; gravity is reserved for vertical object dynamics.
    for (const o of this.objects) {
      o.x += o.vx * dt; o.z += o.vz * dt;
      o.vx *= Math.pow(.16, dt); o.vz *= Math.pow(.16, dt);
      o.x = Math.max(-4.55, Math.min(4.55, o.x));
      o.z = Math.max(-3.2, Math.min(3.2, o.z));
    }
  }

  addNote(text) { this.notes.push({ time: this.clockLabel(), text }); this.notes = this.notes.slice(-30); }
  addEvent(text) { this.events.unshift({ time: this.clockLabel(), text }); this.events = this.events.slice(0, 12); }
  clockLabel() { const m = Math.floor(this.worldTime / 120 * 1440) % 1440; return `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`; }
  emit() { this.onUpdate({ worldTime:this.worldTime, agent:this.agent, objects:this.objects, notes:this.notes, events:this.events, goal:this.goal, status:this.status }); }
}
