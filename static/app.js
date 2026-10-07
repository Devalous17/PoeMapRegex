const input = document.getElementById('build-input');
const analyzeButton = document.getElementById('analyze-button');
const statusLine = document.getElementById('status');
const results = document.getElementById('results');
const profileBox = document.getElementById('profile');
const presetsBox = document.getElementById('presets');
const groupsBox = document.getElementById('mod-groups');

let analysis = null;
const overrides = {};

function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function number(value) {
  return typeof value === 'number' && Number.isFinite(value)
    ? Math.round(value).toLocaleString() : '—';
}

function setStatus(message, isError = false) {
  statusLine.textContent = message;
  statusLine.classList.toggle('error', isError);
}

function renderProfile(profile) {
  profileBox.replaceChildren();
  const title = el('div', 'profile-title');
  title.append(el('strong', '', `${profile.main_skill} ${profile.ascendancy}`));
  title.append(el('small', '', `Level ${profile.level} ${profile.class} · ${profile.game}`));
  profileBox.append(title);
  const stats = [
    ['Damage', profile.damage_type === 'unknown' ? 'Needs review' : profile.damage_type],
    ['Energy Shield', number(profile.energy_shield)],
    ['Life', number(profile.life)],
    ['Chaos Resist', profile.chaos_resistance == null ? '—' : `${profile.chaos_resistance}%`],
  ];
  for (const [label, value] of stats) {
    const item = el('div', 'profile-stat');
    item.append(el('small', '', label), el('strong', '', value));
    profileBox.append(item);
  }
}

function generateRegex(preset) {
  const ratings = {
    safe: ['brick', 'dangerous', 'uncomfortable'],
    balanced: ['brick', 'dangerous'],
    greedy: ['brick'],
  };
  const blocked = analysis.mods.filter(mod => {
    const override = overrides[mod.id];
    return override === 'avoid' || (override !== 'allow' && ratings[preset].includes(mod.rating));
  });
  const query = blocked.length ? `"!${blocked.map(mod => mod.pattern).join('|')}"` : '';
  return { query, count: blocked.length, length: query.length, withinLimit: query.length <= analysis.regex_limit };
}

function renderPresets() {
  presetsBox.replaceChildren();
  const labels = [
    ['safe', 'SAFE', 'Avoid every flagged mod, including uncomfortable ones.'],
    ['balanced', 'BALANCED', 'Avoid build breakers and strong dangers.'],
    ['greedy', 'GREEDY', 'Avoid only mods that look build breaking.'],
  ];
  for (const [key, name, description] of labels) {
    const data = generateRegex(key);
    const card = el('article', `preset-card ${key === 'balanced' ? 'recommended' : ''}`);
    card.append(el('span', 'preset-kicker', key === 'balanced' ? 'RECOMMENDED' : 'PRESET'));
    card.append(el('h3', '', name), el('p', '', description));
    card.append(el('div', 'preset-count', `${data.count} mod${data.count === 1 ? '' : 's'} filtered`));
    card.append(el('div', `regex-box ${data.query ? '' : 'empty'}`, data.query || 'No restrictions for this preset.'));
    const meta = el('div', `regex-meta ${data.withinLimit ? '' : 'warning'}`);
    meta.append(el('span', '', `${data.length} / ${analysis.regex_limit} characters`));
    meta.append(el('span', '', data.withinLimit ? 'Ready to paste' : 'Too long — allow some mods'));
    card.append(meta);
    const copy = el('button', 'copy-button', 'COPY REGEX');
    copy.type = 'button';
    copy.disabled = !data.query || !data.withinLimit;
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(data.query);
        copy.textContent = 'COPIED';
        setTimeout(() => { copy.textContent = 'COPY REGEX'; }, 1800);
      } catch {
        setStatus('Clipboard access failed. Select the regex text and copy it manually.', true);
      }
    });
    card.append(copy);
    presetsBox.append(card);
  }
}

const groupInfo = [
  ['brick', "Can't run", 'Likely to stop this build from functioning'],
  ['dangerous', 'Dangerous', 'Strongly consider avoiding'],
  ['uncomfortable', 'Uncomfortable', 'May make the map feel bad'],
  ['free', 'Free for this build', 'No major interaction detected'],
  ['review', 'Needs review', 'PoB does not prove the interaction'],
];

function renderMods() {
  groupsBox.replaceChildren();
  for (const [rating, title, subtitle] of groupInfo) {
    const mods = analysis.mods.filter(mod => mod.rating === rating);
    if (!mods.length) continue;
    const group = el('section', `mod-group ${rating}`);
    const heading = el('h3');
    heading.append(el('span', '', title), el('span', 'mod-count', String(mods.length).padStart(2, '0')));
    group.append(heading);
    group.append(el('p', 'group-subtitle', subtitle));
    for (const mod of mods) {
      const card = el('article', 'mod-card');
      const top = el('div', 'mod-top');
      top.append(el('strong', '', mod.name));
      const choice = el('select');
      choice.setAttribute('aria-label', `Override ${mod.name}`);
      for (const [value, label] of [['auto', 'AUTO'], ['avoid', 'AVOID'], ['allow', 'ALLOW']]) {
        const option = el('option', '', label);
        option.value = value;
        choice.append(option);
      }
      choice.value = overrides[mod.id] || 'auto';
      choice.addEventListener('change', () => {
        if (choice.value === 'auto') delete overrides[mod.id];
        else overrides[mod.id] = choice.value;
        renderPresets();
      });
      top.append(choice);
      card.append(top, el('p', '', mod.reason));
      group.append(card);
    }
    groupsBox.append(group);
  }
}

async function analyze() {
  const source = input.value.trim();
  if (!source) {
    setStatus('Paste your pobb.in link or PoB export code first.', true);
    input.focus();
    return;
  }
  analyzeButton.disabled = true;
  setStatus('Reading your build…');
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not analyze this build.');
    analysis = data;
    for (const key of Object.keys(overrides)) delete overrides[key];
    renderProfile(data.profile);
    renderPresets();
    renderMods();
    results.hidden = false;
    setStatus('Build analyzed. Review the mod decisions below.');
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    results.hidden = true;
    setStatus(error.message || 'Could not analyze this build.', true);
  } finally {
    analyzeButton.disabled = false;
  }
}

analyzeButton.addEventListener('click', analyze);
input.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') analyze();
});
