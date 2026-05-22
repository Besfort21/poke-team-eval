// ── Constants ────────────────────────────────────────────────────────
const ALL_TYPES = [
  'normal','fire','water','electric','grass','ice','fighting','poison',
  'ground','flying','psychic','bug','rock','ghost','dragon','dark','steel','fairy'
];

const STAT_LABELS = {
  hp:'HP', attack:'ATK', defense:'DEF', sp_atk:'SpA', sp_def:'SpD', speed:'SPE'
};

// ── State ────────────────────────────────────────────────────────────
const state = {
  eval: { gen: 1, team: [], selected: null },
  build: { gen: 1, anchors: [], selected: null },
};

// ── Tab switching ────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// ── Generation picker ────────────────────────────────────────────────
const GENS = [
  { id:1, label:'GEN I',   region:'Kanto'  },
  { id:2, label:'GEN II',  region:'Johto'  },
  { id:3, label:'GEN III', region:'Hoenn'  },
  { id:4, label:'GEN IV',  region:'Sinnoh' },
  { id:5, label:'GEN V',   region:'Unova'  },
  { id:6, label:'GEN VI',  region:'Kalos'  },
  { id:7, label:'GEN VII', region:'Alola'  },
  { id:8, label:'GEN VIII',region:'Galar'  },
  { id:9, label:'GEN IX',  region:'Paldea' },
];

function buildGenPicker(containerId, stateKey) {
  const container = document.getElementById(containerId);
  GENS.forEach(g => {
    const btn = document.createElement('button');
    btn.className = 'gen-btn' + (g.id === 1 ? ' active' : '');
    btn.textContent = g.label;
    btn.title = g.region;
    btn.addEventListener('click', () => {
      container.querySelectorAll('.gen-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state[stateKey].gen = g.id;
      // Clear team when gen changes
      if (stateKey === 'eval') { state.eval.team = []; renderSlots('eval-slots', state.eval.team, 6, removeEvalMon); updateEvalBtn(); }
      if (stateKey === 'build') { state.build.anchors = []; renderSlots('build-slots', state.build.anchors, 5, removeBuildMon); updateBuildBtn(); }
    });
    container.appendChild(btn);
  });
}

buildGenPicker('eval-gen-picker', 'eval');
buildGenPicker('build-gen-picker', 'build');

// ── Slots renderer ───────────────────────────────────────────────────
function renderSlots(containerId, list, maxSlots, removeFn) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';
  for (let i = 0; i < maxSlots; i++) {
    const slot = document.createElement('div');
    slot.className = 'slot' + (list[i] ? ' filled' : '');
    if (list[i]) {
      const mon = list[i];
      const removeBtn = document.createElement('button');
      removeBtn.className = 'slot-remove';
      removeBtn.textContent = '✕';
      removeBtn.addEventListener('click', () => removeFn(i));

      const name = document.createElement('div');
      name.className = 'slot-name';
      name.textContent = mon.name;

      const types = document.createElement('div');
      types.style.display = 'flex';
      types.style.gap = '3px';
      types.style.flexWrap = 'wrap';
      types.style.justifyContent = 'center';
      mon.types.forEach(t => {
        const badge = document.createElement('span');
        badge.className = `type-badge type-${t}`;
        badge.textContent = t;
        types.appendChild(badge);
      });

      slot.appendChild(removeBtn);
      slot.appendChild(name);
      slot.appendChild(types);
    } else {
      const num = document.createElement('div');
      num.className = 'slot-number';
      num.textContent = `SLOT ${i + 1}`;
      slot.appendChild(num);
    }
    container.appendChild(slot);
  }
}

// ── Autocomplete ─────────────────────────────────────────────────────
function setupAutocomplete(inputId, acId, stateKey, onSelect) {
  const input = document.getElementById(inputId);
  const ac = document.getElementById(acId);
  let debounce = null;

  input.addEventListener('input', () => {
    clearTimeout(debounce);
    const q = input.value.trim();
    if (q.length < 2) { ac.classList.remove('open'); ac.innerHTML = ''; return; }
    debounce = setTimeout(async () => {
      const gen = state[stateKey].gen;
      const res = await fetch(`/api/pokemon/search?q=${encodeURIComponent(q)}&gen=${gen}&limit=8`);
      const data = await res.json();
      ac.innerHTML = '';
      if (!data.results.length) { ac.classList.remove('open'); return; }
      data.results.forEach(mon => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';

        const nameEl = document.createElement('span');
        nameEl.className = 'ac-name';
        nameEl.textContent = mon.name;

        const typesEl = document.createElement('span');
        typesEl.style.display = 'flex';
        typesEl.style.gap = '3px';
        mon.types.forEach(t => {
          const b = document.createElement('span');
          b.className = `type-badge type-${t}`;
          b.textContent = t;
          typesEl.appendChild(b);
        });

        const bstEl = document.createElement('span');
        bstEl.style.cssText = 'margin-left:auto;font-size:10px;color:var(--text-muted)';
        bstEl.textContent = `BST ${mon.bst}`;

        item.appendChild(nameEl);
        item.appendChild(typesEl);
        item.appendChild(bstEl);
        item.addEventListener('click', () => {
          input.value = '';
          ac.classList.remove('open');
          ac.innerHTML = '';
          onSelect(mon);
        });
        ac.appendChild(item);
      });
      ac.classList.add('open');
    }, 200);
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !ac.contains(e.target)) {
      ac.classList.remove('open');
    }
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { ac.classList.remove('open'); }
  });
}

// ── Evaluate tab logic ───────────────────────────────────────────────
function removeEvalMon(index) {
  state.eval.team.splice(index, 1);
  renderSlots('eval-slots', state.eval.team, 6, removeEvalMon);
  updateEvalBtn();
}

function updateEvalBtn() {
  document.getElementById('eval-btn').disabled = state.eval.team.length === 0;
}

setupAutocomplete('eval-search', 'eval-autocomplete', 'eval', (mon) => {
  if (state.eval.team.length >= 6) return;
  state.eval.team.push(mon);
  renderSlots('eval-slots', state.eval.team, 6, removeEvalMon);
  updateEvalBtn();
});

document.getElementById('eval-add-btn').addEventListener('click', () => {
  const val = document.getElementById('eval-search').value.trim();
  if (!val) return;
  // Try exact match via autocomplete select
  document.getElementById('eval-search').dispatchEvent(new Event('input'));
});

renderSlots('eval-slots', state.eval.team, 6, removeEvalMon);

// ── Build tab logic ──────────────────────────────────────────────────
function removeBuildMon(index) {
  state.build.anchors.splice(index, 1);
  renderSlots('build-slots', state.build.anchors, 5, removeBuildMon);
  updateBuildBtn();
}

function updateBuildBtn() {
  document.getElementById('build-btn').disabled = state.build.anchors.length === 0;
}

setupAutocomplete('build-search', 'build-autocomplete', 'build', (mon) => {
  if (state.build.anchors.length >= 5) return;
  state.build.anchors.push(mon);
  renderSlots('build-slots', state.build.anchors, 5, removeBuildMon);
  updateBuildBtn();
});

renderSlots('build-slots', state.build.anchors, 5, removeBuildMon);

// BST slider
const bstSlider = document.getElementById('bst-slider');
const bstDisplay = document.getElementById('bst-display');
bstSlider.addEventListener('input', () => { bstDisplay.textContent = bstSlider.value; });

// ── Rendering helpers ────────────────────────────────────────────────
function typeBadge(t) {
  const s = document.createElement('span');
  s.className = `type-badge type-${t}`;
  s.textContent = t;
  return s;
}

function effClass(eff) {
  if (eff === 0)   return 'eff-0';
  if (eff <= 0.5)  return 'eff-half';
  if (eff === 1)   return 'eff-1';
  if (eff === 2)   return 'eff-2';
  return 'eff-4';
}

function effLabel(eff) {
  if (eff === 0)   return '0×';
  if (eff === 0.25) return '¼×';
  if (eff === 0.5) return '½×';
  if (eff === 1)   return '1×';
  if (eff === 2)   return '2×';
  return '4×';
}

function renderReport(report, container) {
  container.innerHTML = '';

  // ── Team table ──
  const teamPanel = document.createElement('div');
  teamPanel.className = 'panel';
  teamPanel.style.gridColumn = '1 / -1';
  teamPanel.innerHTML = `<div class="panel-title">// TEAM OVERVIEW</div>`;

  const table = document.createElement('table');
  table.className = 'team-table';
  table.innerHTML = `<thead><tr>
    <th>POKÉMON</th><th>TYPES</th><th>ROLE</th>
    <th>HP</th><th>ATK</th><th>DEF</th><th>SpA</th><th>SpD</th><th>SPE</th><th>BST</th><th>KEY MOVES</th>
  </tr></thead>`;
  const tbody = document.createElement('tbody');
  report.team.forEach(m => {
    const tr = document.createElement('tr');
    const typesHtml = m.types.map(t => `<span class="type-badge type-${t}">${t}</span>`).join(' ');
    const keyMovesHtml = (m.key_moves || []).map(mv => `
      <span class="type-badge type-${mv.type}" title="${mv.damage_class} · ${mv.power} power">
        ${mv.name.replace('-', ' ')}
      </span>
    `).join(' ');

    tr.innerHTML = `
      <td>${m.name}</td>
      <td>${typesHtml}</td>
      <td style="font-size:11px;color:var(--text-dim)">${m.role}</td>
      <td>${m.stats.hp}</td><td>${m.stats.attack}</td><td>${m.stats.defense}</td>
      <td>${m.stats.sp_atk}</td><td>${m.stats.sp_def}</td><td>${m.stats.speed}</td>
      <td style="color:var(--red-bright)">${m.bst}</td>
      <td style="min-width:160px">${keyMovesHtml}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  teamPanel.appendChild(table);

  // ── Warnings ──
  if (report.roles.warnings.length) {
    report.roles.warnings.forEach(w => {
      const el = document.createElement('div');
      el.className = 'warning';
      el.textContent = '⚠ ' + w;
      teamPanel.appendChild(el);
    });
  }

  const grid = document.createElement('div');
  grid.className = 'results-grid';
  grid.appendChild(teamPanel);

  // ── Role distribution ──
  const rolePanel = document.createElement('div');
  rolePanel.className = 'panel';
  rolePanel.innerHTML = `<div class="panel-title">// ROLE DISTRIBUTION</div>`;
  const maxCount = Math.max(...Object.values(report.roles.distribution));
  Object.entries(report.roles.distribution).forEach(([role, count]) => {
    const row = document.createElement('div');
    row.className = 'role-bar-row';
    const pct = (count / maxCount) * 100;
    row.innerHTML = `
      <span class="role-label">${role}</span>
      <div class="role-bar" style="width:${pct * 0.6}px; max-width:120px"></div>
      <span class="role-count">${count}</span>
    `;
    rolePanel.appendChild(row);
  });
  grid.appendChild(rolePanel);

  // ── Offensive coverage ──
  const offPanel = document.createElement('div');
  offPanel.className = 'panel';
  offPanel.innerHTML = `<div class="panel-title">// OFFENSIVE COVERAGE</div>`;
  const covGrid = document.createElement('div');
  covGrid.className = 'coverage-grid';
  ALL_TYPES.forEach(t => {
    const eff = report.type_coverage.offensive[t] || 0;
    const cell = document.createElement('div');
    cell.className = `coverage-cell ${effClass(eff)}`;
    cell.innerHTML = `<span class="eff">${effLabel(eff)}</span><span>${t}</span>`;
    covGrid.appendChild(cell);
  });
  offPanel.appendChild(covGrid);
  grid.appendChild(offPanel);

  // ── Defensive profile ──
  const defPanel = document.createElement('div');
  defPanel.className = 'panel';
  defPanel.innerHTML = `<div class="panel-title">// DEFENSIVE PROFILE</div>`;

  const sections = [
    { label: 'DANGER (2+ members weak)', types: report.type_coverage.danger_types, cls: 'tag-danger' },
    { label: 'WEAK TO', types: report.type_coverage.weak_to, cls: 'tag-weak' },
    { label: 'IMMUNITIES', types: report.type_coverage.immunities, cls: 'tag-immune' },
    { label: 'RESISTED BY', types: report.type_coverage.strong_against, cls: 'tag-strong' },
  ];

  sections.forEach(({ label, types, cls }) => {
    if (!types.length) return;
    const lbl = document.createElement('div');
    lbl.style.cssText = 'font-family:var(--font-pixel);font-size:6px;color:var(--text-muted);letter-spacing:2px;margin-top:12px;margin-bottom:4px';
    lbl.textContent = label;
    defPanel.appendChild(lbl);
    const tagList = document.createElement('div');
    tagList.className = 'tag-list';
    types.forEach(t => {
      const tag = document.createElement('span');
      tag.className = `tag ${cls}`;
      tag.textContent = t.toUpperCase();
      tagList.appendChild(tag);
    });
    defPanel.appendChild(tagList);
  });

  grid.appendChild(defPanel);

  // ── Speed tiers ──
  const speedPanel = document.createElement('div');
  speedPanel.className = 'panel';
  speedPanel.innerHTML = `<div class="panel-title">// SPEED TIERS</div>`;
  const maxSpeed = report.stats.speed_tiers[0]?.[1] || 1;
  report.stats.speed_tiers.forEach(([name, spd]) => {
    const pct = (spd / maxSpeed) * 100;
    const row = document.createElement('div');
    row.className = 'speed-row';
    row.innerHTML = `
      <span class="speed-name">${name}</span>
      <div class="speed-bar-wrap">
        <div class="speed-bar" style="width:${pct}%"></div>
      </div>
      <span class="speed-val">${spd}</span>
    `;
    speedPanel.appendChild(row);
  });
  grid.appendChild(speedPanel);

  container.appendChild(grid);
}

// ── Evaluate API call ────────────────────────────────────────────────
document.getElementById('eval-btn').addEventListener('click', async () => {
  const container = document.getElementById('results');
  container.innerHTML = `<div class="loading">ANALYSING TEAM...</div>`;

  try {
    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        generation: state.eval.gen,
        pokemon: state.eval.team.map(m => m.name),
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      container.innerHTML = `<div class="error-msg">ERROR: ${err.detail}</div>`;
      return;
    }

    const report = await res.json();
    renderReport(report, container);
  } catch (e) {
    container.innerHTML = `<div class="error-msg">CONNECTION ERROR — is the server running?</div>`;
  }
});

// ── Build API call ───────────────────────────────────────────────────
document.getElementById('build-btn').addEventListener('click', async () => {
  const container = document.getElementById('build-results');
  container.innerHTML = `<div class="loading">BUILDING TEAM...</div>`;

  try {
    const res = await fetch('/api/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        generation: state.build.gen,
        anchors: state.build.anchors.map(m => m.name),
        min_bst: parseInt(bstSlider.value),
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      container.innerHTML = `<div class="error-msg">ERROR: ${err.detail}</div>`;
      return;
    }

    const data = await res.json();
    container.innerHTML = '';

    // Suggestions
    const sugPanel = document.createElement('div');
    sugPanel.className = 'panel';
    sugPanel.style.marginBottom = '24px';
    sugPanel.innerHTML = `<div class="panel-title">// SUGGESTED TEAM</div>`;

    data.explanations.forEach((exp, i) => {
      const card = document.createElement('div');
      const mon = data.team[i];
      card.className = 'suggestion-card' + (i < state.build.anchors.length ? ' anchor' : '');
      card.style.animationDelay = `${i * 80}ms`;

      const header = document.createElement('div');
      header.className = 'suggestion-header';

      const num = document.createElement('span');
      num.className = 'suggestion-num';
      num.textContent = `#${i + 1}`;

      const name = document.createElement('span');
      name.className = 'suggestion-name';
      name.textContent = mon.name;

      const typesEl = document.createElement('span');
      typesEl.style.display = 'flex';
      typesEl.style.gap = '3px';
      mon.types.forEach(t => typesEl.appendChild(typeBadge(t)));

      const bstEl = document.createElement('span');
      bstEl.style.cssText = 'margin-left:auto;font-family:var(--font-pixel);font-size:6px;color:var(--text-muted)';
      bstEl.textContent = `BST ${mon.bst}`;

      header.appendChild(num);
      header.appendChild(name);
      header.appendChild(typesEl);
      header.appendChild(bstEl);

      const reason = document.createElement('div');
      reason.className = 'suggestion-reason';
      // Strip the name prefix from explanation for cleaner display
      reason.textContent = exp.split(': ').slice(1).join(': ') || exp;

      card.appendChild(header);
      card.appendChild(reason);
      sugPanel.appendChild(card);
    });

    container.appendChild(sugPanel);
    renderReport(data.eval_report, container);

  } catch (e) {
    container.innerHTML = `<div class="error-msg">CONNECTION ERROR — is the server running?</div>`;
  }
});