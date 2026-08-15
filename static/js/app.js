const t = key => window.KINKUDOS?.i18n?.[key] || key;

function bindPrimaryTap(target, selector, handler) {
  let startX = 0;
  let startY = 0;
  let last = 0;
  const match = event => event.target.closest?.(selector);
  const run = (event, node) => {
    const now = Date.now();
    if (now - last < 450) {
      event.preventDefault();
      return;
    }
    last = now;
    handler(event, node);
  };
  target.addEventListener("pointerdown", event => {
    if (!match(event)) return;
    startX = event.clientX;
    startY = event.clientY;
  }, { passive: true });
  target.addEventListener("pointerup", event => {
    if (event.pointerType === "mouse") return;
    const node = match(event);
    if (!node) return;
    if (Math.hypot(event.clientX - startX, event.clientY - startY) > 14) return;
    run(event, node);
  });
  target.addEventListener("click", event => {
    const node = match(event);
    if (!node) return;
    run(event, node);
  });
}

document.querySelectorAll('input[type="number"]').forEach(input => {
  const min = Number(input.getAttribute("min"));
  const max = Number(input.getAttribute("max"));
  const signed = min < 0 || max <= 0;
  const limit = signed ? 6 : 5;
  if (!input.hasAttribute("maxlength")) input.setAttribute("maxlength", String(limit));
  if (!input.hasAttribute("inputmode")) input.setAttribute("inputmode", "numeric");
  input.addEventListener("input", () => {
    const raw = input.value;
    const sign = raw.startsWith("-") ? "-" : "";
    const digits = raw.replace(/\D/g, "").slice(0, limit - sign.length);
    const normalized = sign + digits;
    if (raw !== normalized) input.value = normalized;
  });
});

function openPinDialog(childId) {
  const dialog = document.getElementById("pin-dialog");
  const input = document.getElementById("pin-child-id");
  if (!dialog || !input) return;
  input.value = childId;
  dialog.showModal();
  document.getElementById("id_pin")?.focus();
}

document.querySelectorAll("[data-open-pin]").forEach(button => {
  button.addEventListener("click", () => openPinDialog(button.dataset.openPin));
});
bindPrimaryTap(document, "[data-close-dialog], [data-open-dialog]", (_event, button) => {
  if (button.matches("[data-close-dialog]")) {
    button.closest("dialog")?.close();
    return;
  }
  button.closest("dialog")?.close();
  document.getElementById(button.dataset.openDialog)?.showModal();
});
document.querySelectorAll("[data-confirm]").forEach(button => {
  button.addEventListener("click", event => {
    if (!window.confirm(button.dataset.confirm)) event.preventDefault();
  });
});

const setupEmailToggle = document.getElementById("id_configure_smtp");
const setupEmailFields = [...document.querySelectorAll('[id^="id_smtp_"]')];

function syncSetupEmailFields() {
  if (!setupEmailToggle) return;
  const disabled = !setupEmailToggle.checked;
  setupEmailFields.forEach(field => {
    field.disabled = disabled;
    field.closest("p")?.classList.toggle("is-disabled", disabled);
  });
}

setupEmailToggle?.addEventListener("change", syncSetupEmailFields);
syncSetupEmailFields();

const taskSearch = document.querySelector("[data-task-search]");
const taskSearchResults = document.querySelector("[data-task-search-results]");
const taskCards = [...document.querySelectorAll("[data-task-card]")];

function normalizedTaskSearch(value) {
  return value.trim().toLocaleLowerCase(document.documentElement.lang || undefined);
}

function closeTaskSuggestions() {
  if (!taskSearchResults || !taskSearch) return;
  taskSearchResults.hidden = true;
  taskSearchResults.replaceChildren();
  taskSearch.setAttribute("aria-expanded", "false");
  taskSearch.removeAttribute("aria-activedescendant");
}

function selectTaskSuggestion(card) {
  if (!taskSearch || !card) return;
  taskSearch.value = card.dataset.taskSearchText || "";
  updateTaskSearch(false);
  closeTaskSuggestions();
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  window.setTimeout(() => {
    card.querySelector("button:not([disabled]), a, input:not([disabled])")?.focus();
  }, 300);
}

function showTaskSuggestions(matches) {
  if (!taskSearchResults || !taskSearch) return;
  taskSearchResults.replaceChildren();
  matches.slice(0, 8).forEach((card, index) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "task-search-option";
    option.id = `task-search-option-${index}`;
    option.setAttribute("role", "option");
    option.dataset.taskTarget = card.id;
    option.textContent = card.dataset.taskSearchText || "";
    option.addEventListener("pointerdown", event => event.preventDefault());
    option.addEventListener("click", () => selectTaskSuggestion(card));
    taskSearchResults.append(option);
  });
  taskSearchResults.hidden = matches.length === 0;
  taskSearch.setAttribute("aria-expanded", String(matches.length > 0));
}

function updateTaskSearch(showSuggestions = true) {
  if (!taskSearch) return [];
  const query = normalizedTaskSearch(taskSearch.value);
  let visible = 0;
  const matches = [];
  taskCards.forEach(card => {
    const matchesQuery =
      !query || normalizedTaskSearch(card.dataset.taskSearchText || "").includes(query);
    card.hidden = !matchesQuery;
    if (matchesQuery) {
      visible += 1;
      if (query) matches.push(card);
    }
  });
  const empty = document.querySelector("[data-task-search-empty]");
  if (empty) empty.hidden = visible !== 0;
  if (showSuggestions && query) showTaskSuggestions(matches);
  else closeTaskSuggestions();
  return matches;
}

taskSearch?.addEventListener("input", () => updateTaskSearch(true));
taskSearch?.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    event.preventDefault();
    const firstTarget = taskSearchResults
      ?.querySelector("[data-task-target]")
      ?.getAttribute("data-task-target");
    const firstMatch = firstTarget
      ? document.getElementById(firstTarget)
      : updateTaskSearch(false)[0];
    selectTaskSuggestion(firstMatch);
  } else if (event.key === "Escape") {
    closeTaskSuggestions();
  }
});
taskSearch?.addEventListener("focus", () => {
  if (taskSearch.value.trim()) updateTaskSearch(true);
});
taskSearch?.addEventListener("blur", () => {
  window.setTimeout(closeTaskSuggestions, 120);
});

document.querySelector("[data-gift-form]")?.addEventListener("submit", event => {
  const form = event.currentTarget;
  const recipient = form.querySelector("[name=recipient]")?.selectedOptions?.[0]?.textContent || "";
  const amount = form.querySelector("[name=amount]")?.value || "";
  const template = window.KINKUDOS?.i18n?.giftConfirm || "Send {amount} points to {recipient}?";
  const question = template.replace("{amount}", amount).replace("{recipient}", recipient);
  if (!window.confirm(question)) event.preventDefault();
});

document.querySelectorAll(".evidence-form").forEach(form => {
  const input = form.querySelector("[data-evidence-input]");
  const preview = form.querySelector("[data-evidence-preview]");
  const remove = form.querySelector("[data-evidence-remove]");
  const removeField = form.querySelector("[data-remove-evidence]");
  const choose = capture => {
    if (!input) return;
    if (capture) input.setAttribute("capture", "environment");
    else input.removeAttribute("capture");
    input.click();
  };
  form.querySelector("[data-evidence-camera]")?.addEventListener("click", () => choose(true));
  form.querySelector("[data-evidence-gallery]")?.addEventListener("click", () => choose(false));
  input?.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file || !preview) return;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    if (remove) remove.hidden = false;
    if (removeField) removeField.value = "";
  });
  remove?.addEventListener("click", () => {
    if (input) input.value = "";
    if (preview) {
      preview.removeAttribute("src");
      preview.hidden = true;
    }
    remove.hidden = true;
    if (removeField) removeField.value = "on";
  });
});

const lightbox = document.getElementById("evidence-lightbox");
document.addEventListener("click", event => {
  const button = event.target.closest?.("[data-evidence-full]");
  if (!button) return;
  const image = lightbox?.querySelector("[data-lightbox-image]");
  if (!image) return;
  image.src = button.dataset.evidenceFull;
  lightbox.showModal();
});

const parentShell = document.querySelector("[data-parent-shell]");
if (parentShell) {
  const panels = [...parentShell.querySelectorAll("[data-parent-panel]")];
  const links = [...parentShell.querySelectorAll("[data-parent-nav]")];
  const scrollWorkspaceToTop = () => {
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      });
    });
  };
  const manageSectionForHash = id => {
    if (id === "manage-goals" || /^manage-goals-child-\d+$/.test(id)) return "manage-goals";
    if (["manage-tasks", "manage-penalties", "manage-rewards"].includes(id)) return id;
    return "";
  };
  const parentPanelForHash = id => {
    if (panels.some(panel => panel.id === id)) return id;
    if (manageSectionForHash(id)) return "parent-catalogs";
    return panels[0]?.id;
  };
  const showPanel = id => {
    id = parentPanelForHash(id);
    panels.forEach(panel => { panel.hidden = panel.id !== id; });
    links.forEach(link => {
      const active = link.getAttribute("href") === `#${id}`;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  };
  const syncManageTabs = sectionId => {
    parentShell.querySelectorAll(".manage-tabs a").forEach(link => {
      const active = manageSectionForHash(link.hash.slice(1)) === sectionId;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  };
  const openManageSection = id => {
    const sectionId = manageSectionForHash(id) || (id === "parent-catalogs" ? "manage-tasks" : "");
    if (!sectionId) return false;
    const target = document.getElementById(sectionId);
    if (!target) return false;
    parentShell.querySelectorAll("[data-manage-section]").forEach(section => {
      section.hidden = section !== target;
    });
    syncManageTabs(sectionId);
    window.requestAnimationFrame(() => target.scrollIntoView({ behavior: "auto", block: "start" }));
    return true;
  };
  const showRoute = id => {
    showPanel(id);
    if (manageSectionForHash(id)) return openManageSection(id);
    if (parentPanelForHash(id) === "parent-catalogs") return openManageSection("manage-tasks");
    return false;
  };
  bindPrimaryTap(parentShell, "[data-parent-nav]", (event, link) => {
    event.preventDefault();
    const id = link.hash.slice(1);
    window.history.replaceState(window.history.state, "", `#${id}`);
    showRoute(id);
    if (!manageSectionForHash(id)) scrollWorkspaceToTop();
  });
  const initialHash = window.location.hash.slice(1);
  const initialNestedRoute = showRoute(initialHash || panels[0]?.id);
  if (window.location.hash && !initialNestedRoute) scrollWorkspaceToTop();
  window.addEventListener("hashchange", () => {
    const nestedRoute = showRoute(window.location.hash.slice(1));
    if (!nestedRoute) scrollWorkspaceToTop();
  });
}

document.querySelectorAll("[data-parent-goal-target]").forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    window.history.replaceState(window.history.state, "", "#manage-goals");
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    window.setTimeout(() => {
      const target = document.getElementById(`goal-item-${link.dataset.parentGoalTarget}`);
      target?.scrollIntoView({ behavior: "smooth", block: "center" });
      target?.focus({ preventScroll: true });
    }, 80);
  });
});

document.querySelectorAll(".goal-filter a").forEach(link => {
  link.addEventListener("click", event => {
    const match = link.hash.match(/^#manage-goals-child-(\d+)$/);
    if (!match && link.hash !== "#manage-goals") return;
    event.preventDefault();
    document.querySelectorAll(".goal-filter a").forEach(item => item.classList.remove("is-active"));
    link.classList.add("is-active");
    document.querySelectorAll("[data-goal-child]").forEach(row => {
      row.hidden = Boolean(match) && row.dataset.goalChild !== match[1];
    });
  });
});

document.querySelector("[data-history-child-filter] select[name=history_child]")?.addEventListener("change", event => {
  const select = event.currentTarget;
  const form = select.form;
  if (!form || form.dataset.submitting === "true") return;
  form.dataset.submitting = "true";
  form.classList.add("is-loading");
  form.setAttribute("aria-busy", "true");
  select.disabled = true;
  const url = new URL(window.location.href);
  if (select.value) url.searchParams.set("history_child", select.value);
  else url.searchParams.delete("history_child");
  url.searchParams.delete("history_page");
  url.hash = "parent-history";
  window.location.assign(url.toString());
});

document.querySelectorAll("[data-remove-history-filter]").forEach(button => {
  button.addEventListener("click", () => {
    const url = new URL(window.location.href);
    url.searchParams.delete(button.dataset.removeHistoryFilter);
    if (button.dataset.removeHistoryFilter === "history_date") {
      url.searchParams.delete("history_start");
      url.searchParams.delete("history_end");
    }
    url.searchParams.delete("history_page");
    url.hash = "parent-history";
    window.location.assign(url.toString());
  });
});

function clearHistoryFilters() {
  const url = new URL(window.location.href);
  ["history_child", "history_activity", "history_date", "history_start", "history_end", "history_page"]
    .forEach(key => url.searchParams.delete(key));
  url.hash = "parent-history";
  window.location.assign(url.toString());
}

document.querySelectorAll("[data-clear-history-filters]").forEach(button => {
  button.addEventListener("click", () => {
    if (button.disabled) return;
    button.disabled = true;
    clearHistoryFilters();
  });
});

const historyFilterForm = document.querySelector("[data-history-filter-form]");
if (historyFilterForm) {
  const dateSelect = historyFilterForm.querySelector("[name=history_date]");
  const customRange = historyFilterForm.querySelector("[data-history-custom-range]");
  const dateInputs = [...historyFilterForm.querySelectorAll("[name=history_start], [name=history_end]")];
  const dateError = historyFilterForm.querySelector("[data-history-date-error]");
  const syncHistoryDateFields = ({ clear = false } = {}) => {
    const custom = dateSelect?.value === "custom";
    if (clear && !custom) dateInputs.forEach(input => { input.value = ""; });
    dateInputs.forEach(input => { input.disabled = !custom; });
    if (customRange) customRange.hidden = !custom;
    if (!custom && dateError) {
      dateError.hidden = true;
      dateError.textContent = "";
    }
  };
  dateSelect?.addEventListener("change", () => syncHistoryDateFields({ clear: true }));
  dateInputs.forEach(input => {
    input.addEventListener("change", () => {
      if (dateSelect) dateSelect.value = "custom";
      syncHistoryDateFields();
    });
  });
  historyFilterForm.querySelector("[data-history-reset]")?.addEventListener("click", () => {
    historyFilterForm.querySelector("[name=history_child]").value = "";
    historyFilterForm.querySelector("[name=history_activity]").value = "";
    dateSelect.value = "any";
    syncHistoryDateFields({ clear: true });
  });
  historyFilterForm.addEventListener("submit", event => {
    if (dateSelect?.value === "custom") {
      const [start, end] = dateInputs.map(input => input.value);
      if (start && end && start > end) {
        event.preventDefault();
        if (dateError) {
          dateError.textContent = t("historyDateOrder");
          dateError.hidden = false;
        }
        dateInputs[0].focus();
        return;
      }
    }
    historyFilterForm.querySelectorAll('[name="history_page"]').forEach(input => input.remove());
  });
  syncHistoryDateFields();
}

{
  const url = new URL(window.location.href);
  const hasDates = url.searchParams.has("history_start") || url.searchParams.has("history_end");
  if (hasDates && url.searchParams.get("history_date") !== "custom") {
    url.searchParams.set("history_date", "custom");
    window.history.replaceState(null, "", url.toString());
  } else if (url.searchParams.get("history_date") === "any") {
    url.searchParams.delete("history_date");
    window.history.replaceState(null, "", url.toString());
  }
}

function celebrate() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const layer = document.createElement("div");
  const theme = [...document.body.classList].find(name => name.startsWith("theme-")) || "theme-neutral";
  layer.className = `confetti-layer ${theme}`;
  for (let index = 0; index < 28; index += 1) {
    const piece = document.createElement("i");
    piece.style.setProperty("--x", `${Math.random() * 100}vw`);
    piece.style.setProperty("--delay", `${Math.random() * 0.5}s`);
    piece.style.setProperty("--spin", `${Math.random() * 720 - 360}deg`);
    layer.append(piece);
  }
  document.body.append(layer);
  window.setTimeout(() => layer.remove(), 2600);
}

function prepareThemeSound() {
  if (localStorage.getItem("kinkudos-sound") === "off") return;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  const context = new AudioContext();
  context.resume?.();
  const unlock = context.createOscillator();
  const silent = context.createGain();
  silent.gain.value = 0.0001;
  unlock.connect(silent).connect(context.destination);
  unlock.start();
  unlock.stop(context.currentTime + 0.01);
  return context;
}

function playThemeSound(effect = "task", preparedContext = null) {
  if (localStorage.getItem("kinkudos-sound") === "off") return;
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;
  const context = preparedContext || new AudioContext();
  context.resume?.();
  const theme = document.body.classList.contains("theme-magic_academy") ? "magic"
    : document.body.classList.contains("theme-block_world") ? "block"
      : document.body.classList.contains("theme-hero_hq") ? "hero"
        : document.body.classList.contains("theme-art_studio") ? "art"
          : document.body.classList.contains("theme-panda_pet") ? "panda" : "neutral";
  const resolvedTheme = document.body.classList.contains("theme-blockville") ? "blockville" : theme;
  const isReward = effect === "reward";
  const notes = resolvedTheme === "blockville"
    ? [392, 523, 659, 784]
    : theme === "hero"
    ? [196, 294, 392, 587]
    : theme === "art"
      ? [523, 659, 784]
      : theme === "panda"
        ? [262, 330, 392]
        : theme === "magic" && !isReward
    ? [294, 247, 294, 220]
    : theme === "block" && isReward
      ? [110, 147, 196]
      : theme === "block"
        ? [130, 196, 262]
        : [330, 440, 523];
  notes.forEach((frequency, index) => {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = ["block", "hero", "blockville"].includes(resolvedTheme) ? "square" : ["magic", "art", "panda"].includes(resolvedTheme) ? "sine" : "triangle";
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0.0001, context.currentTime);
    const spacing = theme === "magic" && !isReward ? 0.16 : 0.1;
    const peak = theme === "magic" ? 0.045 : 0.07;
    gain.gain.exponentialRampToValueAtTime(peak, context.currentTime + 0.02 + index * spacing);
    gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.3 + index * spacing);
    oscillator.connect(gain).connect(context.destination);
    oscillator.start(context.currentTime + index * spacing);
    oscillator.stop(context.currentTime + 0.4 + index * spacing);
  });
  window.setTimeout(() => context.close(), 1200);
}

const successMessage = document.querySelector(".message-task-success, .message-reward-success");
let skipRedirectEffect = false;
try {
  skipRedirectEffect = sessionStorage.getItem("kinkudos-skip-success-effect") === "1";
  sessionStorage.removeItem("kinkudos-skip-success-effect");
} catch (_) {}
if (successMessage && !skipRedirectEffect) {
  celebrate();
  playThemeSound(successMessage.classList.contains("message-reward-success") ? "reward" : "task");
}

document.querySelectorAll("form[data-success-effect]").forEach(form => {
  form.addEventListener("submit", async event => {
    if (!window.fetch || form.dataset.submitting === "true") return;
    if (!form.checkValidity()) {
      event.preventDefault();
      form.reportValidity();
      return;
    }

    event.preventDefault();
    form.dataset.submitting = "true";
    form.setAttribute("aria-busy", "true");
    const submitButtons = [...form.querySelectorAll('button[type="submit"]')];
    submitButtons.forEach(button => { button.disabled = true; });
    const soundContext = prepareThemeSound();

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          "Accept": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        soundContext?.close();
        window.location.assign(payload.redirect_url || window.location.href);
        return;
      }

      celebrate();
      playThemeSound(payload.effect || form.dataset.successEffect || "task", soundContext);
      try {
        sessionStorage.setItem("kinkudos-skip-success-effect", "1");
      } catch (_) {}
      window.setTimeout(
        () => window.location.assign(payload.redirect_url || window.location.href),
        900,
      );
    } catch (_) {
      soundContext?.close();
      HTMLFormElement.prototype.submit.call(form);
    }
  });
});

const soundToggle = document.getElementById("sound-toggle");
function refreshSoundToggle() {
  if (!soundToggle) return;
  const muted = localStorage.getItem("kinkudos-sound") === "off";
  const iconUse = soundToggle.querySelector("use");
  iconUse?.setAttribute("href", muted ? "#icon-volume-xmark" : "#icon-volume-high");
  soundToggle.classList.toggle("sound-enabled", !muted);
  soundToggle.classList.toggle("sound-disabled", muted);
  const label = muted ? window.KINKUDOS?.i18n?.turnSoundsOn : window.KINKUDOS?.i18n?.turnSoundsOff;
  if (label) {
    soundToggle.setAttribute("aria-label", label);
    soundToggle.setAttribute("title", label);
  }
  soundToggle.setAttribute("aria-pressed", String(!muted));
}
soundToggle?.addEventListener("click", () => {
  localStorage.setItem("kinkudos-sound", localStorage.getItem("kinkudos-sound") === "off" ? "on" : "off");
  refreshSoundToggle();
});
refreshSoundToggle();

const lotteryDialog = document.querySelector("[data-lottery-dialog]");
if (lotteryDialog) {
  const ticket = lotteryDialog.querySelector("[data-scratch-ticket]");
  const canvas = lotteryDialog.querySelector("[data-scratch-surface]");
  const particles = lotteryDialog.querySelector("[data-scratch-particles]");
  const progress = lotteryDialog.querySelector("[data-scratch-progress]");
  const result = lotteryDialog.querySelector("[data-lottery-result]");
  const resultTitle = lotteryDialog.querySelector("[data-lottery-result-title]");
  const resultCopy = lotteryDialog.querySelector("[data-lottery-result-copy]");
  const values = [...lotteryDialog.querySelectorAll("[data-lottery-cell]")];
  const storageKey = `kinkudos-lottery-${lotteryDialog.dataset.ticketId}`;
  const revealed = new Set();
  let drawing = false;
  let completed = false;
  let lastPoint = null;
  let scratchSoundAt = 0;

  try {
    JSON.parse(localStorage.getItem(storageKey) || "[]").forEach(index => revealed.add(index));
  } catch (_) {}

  function saveScratchState() {
    try {
      localStorage.setItem(storageKey, JSON.stringify([...revealed]));
    } catch (_) {}
  }

  function canvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function scratchSound() {
    if (localStorage.getItem("kinkudos-sound") === "off") return;
    const now = performance.now();
    if (now - scratchSoundAt < 65) return;
    scratchSoundAt = now;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const context = new AudioContext();
    const length = Math.max(1, Math.floor(context.sampleRate * 0.045));
    const buffer = context.createBuffer(1, length, context.sampleRate);
    const samples = buffer.getChannelData(0);
    for (let index = 0; index < length; index += 1) {
      samples[index] = (Math.random() * 2 - 1) * (1 - index / length);
    }
    const source = context.createBufferSource();
    const filter = context.createBiquadFilter();
    const gain = context.createGain();
    source.buffer = buffer;
    filter.type = "bandpass";
    filter.frequency.value = 1700;
    gain.gain.value = 0.025;
    source.connect(filter).connect(gain).connect(context.destination);
    source.start();
    source.onended = () => context.close();
  }

  function shedParticle(point) {
    if (!particles || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const particle = document.createElement("i");
    particle.style.left = `${point.x}px`;
    particle.style.top = `${point.y}px`;
    particle.style.setProperty("--particle-x", `${Math.random() * 30 - 15}px`);
    particle.style.setProperty("--particle-y", `${Math.random() * 24 + 8}px`);
    particles.append(particle);
    window.setTimeout(() => particle.remove(), 480);
  }

  function eraseLine(from, to) {
    const context = canvas.getContext("2d");
    context.save();
    context.globalCompositeOperation = "destination-out";
    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = Math.max(30, canvas.clientWidth / 10);
    context.beginPath();
    context.moveTo(from.x, from.y);
    context.lineTo(to.x, to.y);
    context.stroke();
    context.restore();
    scratchSound();
    shedParticle(to);
  }

  function cellBounds(index, physical = false) {
    const column = index % 3;
    const row = Math.floor(index / 3);
    const width = physical ? canvas.width : canvas.clientWidth;
    const height = physical ? canvas.height : canvas.clientHeight;
    return {
      x: column * width / 3,
      y: row * height / 3,
      width: width / 3,
      height: height / 3,
    };
  }

  function applyBoardValues(board) {
    values.forEach((cell, index) => {
      const value = Number(board[index] ?? 0);
      cell.dataset.lotteryValue = String(value);
      cell.textContent = value > 0 ? `+${value}` : String(value);
      cell.classList.toggle("scratch-positive", value > 0);
      cell.classList.toggle("scratch-negative", value <= 0);
      cell.classList.remove("scratch-hidden");
      cell.removeAttribute("aria-hidden");
    });
  }

  function clearCell(index) {
    const context = canvas.getContext("2d");
    const bounds = cellBounds(index);
    context.clearRect(bounds.x, bounds.y, bounds.width, bounds.height);
    values[index]?.classList.add("scratch-revealed");
  }

  function coveredRatio(index) {
    const context = canvas.getContext("2d", { willReadFrequently: true });
    const bounds = cellBounds(index, true);
    const image = context.getImageData(
      Math.floor(bounds.x),
      Math.floor(bounds.y),
      Math.max(1, Math.floor(bounds.width)),
      Math.max(1, Math.floor(bounds.height)),
    );
    let erased = 0;
    let sampled = 0;
    for (let pixel = 3; pixel < image.data.length; pixel += 32) {
      sampled += 1;
      if (image.data[pixel] < 80) erased += 1;
    }
    return sampled ? erased / sampled : 0;
  }

  function updateProgress() {
    if (progress) {
      progress.textContent = lotteryDialog.dataset.progressText.replace(
        "{count}",
        String(revealed.size),
      );
    }
  }

  async function finishTicket() {
    if (completed || revealed.size !== 9) return;
    completed = true;
    canvas.classList.add("scratch-finished");
    try {
      const response = await fetch(lotteryDialog.dataset.revealUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": window.KINKUDOS.csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error("Lottery reveal failed");
      if (!Array.isArray(payload.values) || payload.values.length !== values.length) {
        throw new Error("Lottery board missing");
      }
      applyBoardValues(payload.values);
      values.forEach(value => {
        if (Number(value.dataset.lotteryValue) === payload.matching_value && payload.matching_value !== 0) {
          value.classList.add("scratch-match");
        }
      });
      let title = lotteryDialog.dataset.resultNone;
      if (payload.delta > 0) {
        title = lotteryDialog.dataset.resultWin.replace("{amount}", `+${payload.delta}`);
        celebrate();
        playThemeSound("reward");
      } else if (payload.delta < 0) {
        title = lotteryDialog.dataset.resultLoss.replace("{amount}", String(Math.abs(payload.delta)));
      } else if (payload.matching_value < 0) {
        title = lotteryDialog.dataset.resultProtected;
      }
      resultTitle.textContent = title;
      resultCopy.textContent = lotteryDialog.dataset.resultBalance.replace(
        "{balance}",
        String(payload.balance),
      );
      if (payload.matching_value < 0 && payload.delta !== payload.matching_value) {
        resultCopy.textContent += ` ${lotteryDialog.dataset.resultLimited}`;
      }
      result.hidden = false;
      progress.hidden = true;
      document.querySelector(".balance-orb strong").textContent = payload.balance;
      try {
        localStorage.removeItem(storageKey);
      } catch (_) {}
    } catch (_) {
      completed = false;
      resultTitle.textContent = lotteryDialog.dataset.resultError;
      resultCopy.textContent = "";
      result.hidden = false;
    }
  }

  function checkCells() {
    values.forEach((_value, index) => {
      if (!revealed.has(index) && coveredRatio(index) >= 0.55) {
        revealed.add(index);
        clearCell(index);
        navigator.vibrate?.(8);
      }
    });
    saveScratchState();
    updateProgress();
    finishTicket();
  }

  function paintSurface() {
    const rect = ticket.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.round(rect.width * ratio));
    canvas.height = Math.max(1, Math.round(rect.height * ratio));
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    const context = canvas.getContext("2d");
    context.scale(ratio, ratio);
    const gradient = context.createLinearGradient(0, 0, rect.width, rect.height);
    gradient.addColorStop(0, "#8d949b");
    gradient.addColorStop(0.45, "#e6eaed");
    gradient.addColorStop(1, "#777f87");
    context.fillStyle = gradient;
    context.fillRect(0, 0, rect.width, rect.height);
    for (let index = 0; index < Math.floor(rect.width * rect.height / 38); index += 1) {
      const shade = 125 + Math.floor(Math.random() * 100);
      context.fillStyle = `rgba(${shade},${shade},${shade},${Math.random() * 0.26})`;
      context.fillRect(Math.random() * rect.width, Math.random() * rect.height, 1.5, 1.5);
    }
    context.strokeStyle = "rgba(48, 55, 61, .34)";
    context.lineWidth = 2;
    for (let index = 1; index < 3; index += 1) {
      context.beginPath();
      context.moveTo(index * rect.width / 3, 0);
      context.lineTo(index * rect.width / 3, rect.height);
      context.stroke();
      context.beginPath();
      context.moveTo(0, index * rect.height / 3);
      context.lineTo(rect.width, index * rect.height / 3);
      context.stroke();
    }
    revealed.forEach(clearCell);
    updateProgress();
    finishTicket();
  }

  canvas.addEventListener("pointerdown", event => {
    if (completed) return;
    drawing = true;
    lastPoint = canvasPoint(event);
    canvas.setPointerCapture(event.pointerId);
    eraseLine(lastPoint, lastPoint);
  });
  canvas.addEventListener("pointermove", event => {
    if (!drawing || completed) return;
    const point = canvasPoint(event);
    eraseLine(lastPoint, point);
    lastPoint = point;
  });
  const stopDrawing = event => {
    if (!drawing) return;
    drawing = false;
    if (event.pointerId !== undefined && canvas.hasPointerCapture(event.pointerId)) {
      canvas.releasePointerCapture(event.pointerId);
    }
    checkCells();
  };
  canvas.addEventListener("pointerup", stopDrawing);
  canvas.addEventListener("pointercancel", stopDrawing);
  canvas.addEventListener("keydown", event => {
    if (!["Enter", " "].includes(event.key) || completed) return;
    event.preventDefault();
    const next = values.findIndex((_value, index) => !revealed.has(index));
    if (next >= 0) {
      revealed.add(next);
      clearCell(next);
      saveScratchState();
      updateProgress();
      finishTicket();
    }
  });
  canvas.tabIndex = 0;
  document.querySelectorAll('[data-open-dialog="lottery-ticket-dialog"]').forEach(button => {
    button.addEventListener("click", () => window.requestAnimationFrame(paintSurface));
  });
  if (window.location.hash === "#prizai") {
    lotteryDialog.showModal();
    window.requestAnimationFrame(paintSurface);
  }
}

function dismissMessage(message) {
  if (!message || message.classList.contains("is-hiding")) return;
  message.classList.add("is-hiding");
  window.setTimeout(() => message.remove(), 220);
}

document.querySelectorAll("[data-message]").forEach(message => {
  message.querySelector("[data-dismiss-message]")?.addEventListener(
    "click",
    () => dismissMessage(message)
  );
  window.setTimeout(() => dismissMessage(message), 5000);
});

const closeCatalogEdit = form => {
  if (!form) return;
  form.hidden = true;
  form.closest(".catalog-row, .goal-manage-row")?.classList.remove("is-editing");
  const key = form.id.replace(/^edit-/, "");
  const toggle = document.querySelector(`[data-toggle-edit="${key}"]`);
  toggle?.setAttribute("aria-expanded", "false");
};

document.querySelectorAll("[data-toggle-edit]").forEach(button => {
  button.addEventListener("click", () => {
    const form = document.getElementById(`edit-${button.dataset.toggleEdit}`);
    if (!form) return;
    const opening = form.hidden;
    document.querySelectorAll(".catalog-edit-form").forEach(other => {
      if (other !== form) closeCatalogEdit(other);
    });
    form.hidden = !opening;
    button.setAttribute("aria-expanded", String(opening));
    form.closest(".catalog-row, .goal-manage-row")?.classList.toggle("is-editing", opening);
    if (opening) form.querySelector("input, select, textarea")?.focus();
  });
});

document.querySelectorAll("[data-cancel-edit]").forEach(button => {
  button.addEventListener("click", () => closeCatalogEdit(button.closest(".catalog-edit-form")));
});

const accountCreateType = document.querySelector("[data-account-create-type]");
if (accountCreateType) {
  const accountCreateForms = [...document.querySelectorAll("[data-account-create-form]")];
  const syncAccountCreateForm = () => {
    accountCreateForms.forEach(form => {
      form.hidden = form.dataset.accountCreateForm !== accountCreateType.value;
    });
  };
  accountCreateType.addEventListener("change", syncAccountCreateForm);
  syncAccountCreateForm();
}

document.querySelectorAll("dialog[data-reset-on-close]").forEach(dialog => {
  dialog.addEventListener("close", () => dialog.querySelector("form")?.reset());
});

document.querySelectorAll("[data-goal-add-dialog]").forEach(dialog => {
  const input = dialog.querySelector("[data-goal-amount-input]");
  const after = dialog.querySelector("[data-goal-after]");
  if (!input || !after) return;
  const saved = Number(dialog.dataset.goalSaved || 0);
  const target = Number(dialog.dataset.goalTarget || 0);
  const available = Math.max(Number(dialog.dataset.goalAvailable || 0), 0);
  const max = Math.max(Math.min(available, target - saved), 0);
  input.max = String(max);
  const updatePreview = () => {
    const amount = Math.max(Number(input.value || 0), 0);
    after.textContent = String(Math.max(available - Math.min(amount, max), 0));
    input.setCustomValidity(amount > max ? t("goalAmountTooHigh").replace("{max}", max) : "");
  };
  dialog.querySelectorAll("[data-goal-quick-amount]").forEach(button => {
    button.addEventListener("click", () => {
      input.value = String(Math.min(Number(button.dataset.goalQuickAmount), max));
      updatePreview();
      input.focus();
    });
  });
  dialog.querySelector("[data-goal-quick-all]")?.addEventListener("click", () => {
    input.value = String(max);
    updatePreview();
    input.focus();
  });
  input.addEventListener("input", updatePreview);
  updatePreview();
});

document.querySelectorAll("[data-proposal-form]").forEach(form => {
  const type = form.querySelector("[name=proposal_type]");
  const goalMode = form.querySelector("[data-proposal-goal-mode]");
  const syncProposalType = () => {
    const isGoal = type?.value === "goal";
    if (goalMode) {
      goalMode.hidden = !isGoal;
      goalMode.disabled = !isGoal;
    }
    goalMode?.querySelectorAll("[name=goal_mode]").forEach(input => {
      input.required = isGoal;
      if (!isGoal) input.checked = false;
    });
  };
  type?.addEventListener("change", syncProposalType);
  syncProposalType();
});

document.querySelectorAll(".language-switcher-menu").forEach(form => {
  form.addEventListener("submit", () => {
    const next = form.querySelector("[name=next]");
    if (next) next.value = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  });
});

function urlBase64ToUint8Array(value) {
  const padding = "=".repeat((4 - value.length % 4) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(base64), char => char.charCodeAt(0));
}

const pushButton = document.getElementById("enable-push");
const pushHelpDialog = document.getElementById("push-help-dialog");
const pushHelpText = pushHelpDialog?.querySelector("[data-push-help-text]");
function isIosDevice() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
}

function isStandaloneApp() {
  return window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
}

function showPushHelp(reason = "unsupported") {
  if (!pushHelpDialog || !pushHelpText) return;
  if (isIosDevice() && !isStandaloneApp()) {
    pushHelpText.textContent = t("iosInstall");
  } else if (reason === "denied") {
    pushHelpText.textContent = t("notificationsDenied");
  } else {
    pushHelpText.textContent = t("notificationsUnsupportedHelp");
  }
  pushHelpDialog.showModal();
}

function supportsPush() {
  return Boolean(
    window.KINKUDOS.vapidPublicKey
    && "serviceWorker" in navigator
    && "PushManager" in window
    && "Notification" in window
  );
}

function setPushState(state, label) {
  if (!pushButton) return;
  pushButton.classList.remove(
    "push-checking",
    "push-enabled",
    "push-disabled",
    "push-install",
    "push-unsupported"
  );
  pushButton.classList.add(`push-${state}`);
  pushButton.querySelector("[data-push-label]").textContent = label;
  pushButton.setAttribute("aria-pressed", String(state === "enabled"));
  pushButton.title = label;
}

async function getPushSubscription() {
  if (!supportsPush()) {
    return null;
  }
  const registration = await navigator.serviceWorker.ready;
  return registration.pushManager.getSubscription();
}

async function refreshPushState() {
  if (!pushButton) return;
  if (isIosDevice() && !isStandaloneApp()) {
    setPushState("install", t("installForNotifications"));
    pushButton.dataset.pushMode = "install";
    pushButton.disabled = false;
    return;
  }
  if (!supportsPush()) {
    setPushState("unsupported", t("notificationsUnsupported"));
    pushButton.dataset.pushMode = "unsupported";
    pushButton.disabled = false;
    return;
  }
  if (Notification.permission === "denied") {
    setPushState("disabled", t("notificationsBlocked"));
    pushButton.dataset.pushMode = "denied";
    return;
  }
  const subscription = await getPushSubscription();
  if (subscription && Notification.permission === "granted") {
    setPushState("enabled", t("notificationsEnabled"));
    pushButton.dataset.pushMode = "enabled";
  } else {
    setPushState("disabled", t("notificationsDisabled"));
    pushButton.dataset.pushMode = "disabled";
  }
}

async function enablePush() {
  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    await refreshPushState();
    return;
  }
  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(window.KINKUDOS.vapidPublicKey)
    });
  }
  const response = await fetch(window.KINKUDOS.pushUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": window.KINKUDOS.csrfToken },
    body: JSON.stringify(subscription)
  });
  if (!response.ok) throw new Error("Push subscription failed");
  setPushState("enabled", t("notificationsEnabled"));
}

async function disablePush(subscription) {
  const response = await fetch(window.KINKUDOS.pushUnsubscribeUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": window.KINKUDOS.csrfToken },
    body: JSON.stringify({ endpoint: subscription.endpoint })
  });
  if (!response.ok) throw new Error("Push unsubscribe failed");
  await subscription.unsubscribe();
  setPushState("disabled", t("notificationsDisabled"));
}

pushButton?.addEventListener("click", () => {
  if (pushButton.dataset.pushMode === "install") {
    showPushHelp("install");
    return;
  }
  if (pushButton.dataset.pushMode === "unsupported") {
    showPushHelp("unsupported");
    return;
  }
  if (pushButton.dataset.pushMode === "denied") {
    showPushHelp("denied");
    return;
  }
  pushButton.disabled = true;
  getPushSubscription()
    .then(subscription => subscription ? disablePush(subscription) : enablePush())
    .catch(() => alert(t("notificationsFailed")))
    .finally(() => {
      pushButton.disabled = false;
      refreshPushState().catch(() => {});
    });
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js", { updateViaCache: "none" })
      .then(() => refreshPushState())
      .catch(() => setPushState("unsupported", t("notificationsUnsupported")));
  });
} else {
  setPushState("unsupported", t("notificationsUnsupported"));
}

document.querySelectorAll("form[data-single-submit]").forEach(form => {
  form.addEventListener("submit", () => {
    const submitter = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitter) submitter.disabled = true;
  });
});

if (document.body.classList.contains("session-sensitive-page")) {
  window.addEventListener("pageshow", event => {
    if (event.persisted) window.location.reload();
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    fetch(window.location.href, {
      cache: "no-store",
      credentials: "same-origin",
      headers: { Accept: "text/html" },
    }).then(response => {
      if (response.redirected) window.location.assign(response.url);
    }).catch(() => {});
  });
}

const REFRESH_INTERVAL_MS = 10000;
const REFRESH_MAX_BACKOFF_MS = 60000;
const REFRESH_REQUEST_TIMEOUT_MS = 8000;
const STATE_CHANGED_MESSAGE = "kinkudos-state-changed";

function refreshBackoffDelay(failures) {
  return Math.min(REFRESH_INTERVAL_MS * (2 ** failures), REFRESH_MAX_BACKOFF_MS);
}

const childStateUrl = window.KINKUDOS?.childStateUrl;
let childStateSignature = window.KINKUDOS?.childStateSignature || "";
let childRefreshDeferred = false;
let childStateRequestRunning = false;
let childStateRequestController = null;
let childRefreshTimer = null;
let childRefreshFailures = 0;
let childRefreshForcePending = false;
let childRefreshStopped = false;

function childPageHasUnsavedWork() {
  return Boolean(
    document.querySelector("dialog[open]") ||
    document.querySelector("form[data-child-form-dirty='true']")
  );
}

function reloadChildPageWhenSafe() {
  if (childPageHasUnsavedWork()) {
    childRefreshDeferred = true;
    return;
  }
  window.location.reload();
}

function stopChildRefresh() {
  childRefreshStopped = true;
  if (childRefreshTimer !== null) window.clearTimeout(childRefreshTimer);
  childRefreshTimer = null;
  childStateRequestController?.abort();
}

function scheduleChildStateCheck(delay = REFRESH_INTERVAL_MS) {
  if (
    !childStateUrl ||
    childRefreshStopped ||
    document.visibilityState !== "visible"
  ) return;
  if (childRefreshTimer !== null) window.clearTimeout(childRefreshTimer);
  childRefreshTimer = window.setTimeout(() => {
    childRefreshTimer = null;
    checkChildState();
  }, delay);
}

function forceChildStateCheck() {
  if (!childStateUrl || childRefreshStopped || document.visibilityState !== "visible") return;
  if (childStateRequestRunning) {
    childRefreshForcePending = true;
    childStateRequestController?.abort();
    return;
  }
  scheduleChildStateCheck(0);
}

async function checkChildState() {
  if (
    !childStateUrl ||
    childRefreshStopped ||
    document.visibilityState !== "visible" ||
    childStateRequestRunning
  ) return;
  childStateRequestRunning = true;
  const controller = new AbortController();
  childStateRequestController = controller;
  const timeout = window.setTimeout(() => controller.abort(), REFRESH_REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(childStateUrl, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (
      response.redirected ||
      response.status === 401 ||
      response.status === 403 ||
      !response.headers.get("content-type")?.includes("application/json")
    ) {
      stopChildRefresh();
      return;
    }
    if (!response.ok) throw new Error(`Child state request failed: ${response.status}`);
    const state = await response.json();
    childRefreshFailures = 0;
    if (!childStateSignature) {
      childStateSignature = state.signature;
    } else if (state.signature && state.signature !== childStateSignature) {
      childStateSignature = state.signature;
      reloadChildPageWhenSafe();
    }
  } catch (error) {
    if (error.name !== "AbortError") childRefreshFailures += 1;
  } finally {
    window.clearTimeout(timeout);
    if (childStateRequestController === controller) childStateRequestController = null;
    childStateRequestRunning = false;
    if (childRefreshForcePending && !childRefreshStopped) {
      childRefreshForcePending = false;
      scheduleChildStateCheck(0);
    } else {
      scheduleChildStateCheck(refreshBackoffDelay(childRefreshFailures));
    }
  }
}

if (childStateUrl) {
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("input", () => {
      form.dataset.childFormDirty = "true";
    });
    form.addEventListener("change", () => {
      form.dataset.childFormDirty = "true";
    });
  });
  document.addEventListener("close", () => {
    if (childRefreshDeferred && !childPageHasUnsavedWork()) {
      childRefreshDeferred = false;
      window.location.reload();
    }
  }, true);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") forceChildStateCheck();
    else if (childRefreshTimer !== null) {
      window.clearTimeout(childRefreshTimer);
      childRefreshTimer = null;
    }
  });
  window.addEventListener("focus", forceChildStateCheck);
  window.addEventListener("pageshow", forceChildStateCheck);
  window.addEventListener("online", forceChildStateCheck);
  window.addEventListener("pagehide", () => childStateRequestController?.abort());
  window.addEventListener("beforeunload", () => childStateRequestController?.abort());
  navigator.serviceWorker?.addEventListener("message", event => {
    if (event.data?.type === STATE_CHANGED_MESSAGE) forceChildStateCheck();
  });
  scheduleChildStateCheck();
}

const parentWorkspace = document.querySelector("[data-parent-shell]");
const initialPendingFragment = document.querySelector("[data-pending-requests-fragment]");
const parentStateUrl = parentWorkspace && initialPendingFragment
  ? window.KINKUDOS?.parentStateUrl
  : "";
const parentRefreshStatus = document.querySelector("[data-parent-refresh-status]");
const parentRefreshMessage = parentRefreshStatus?.querySelector("[data-parent-refresh-message]");
const applyPendingRefreshButton = parentRefreshStatus?.querySelector("[data-apply-pending-refresh]");
let parentStateRevision = initialPendingFragment?.dataset.pendingRevision || "";
let parentStateCount = Number(initialPendingFragment?.dataset.pendingCount || 0);
let parentStateRequestRunning = false;
let parentStateRequestController = null;
let parentStateTimer = null;
let parentStateFailures = 0;
let parentStateForcePending = false;
let parentStateStopped = false;
let deferredPendingHtml = "";

function currentPendingFragment() {
  return document.querySelector("[data-pending-requests-fragment]");
}

function pendingRequestsHaveActiveInteraction(fragment) {
  return Boolean(
    fragment && (
      fragment.contains(document.activeElement) ||
      fragment.querySelector("dialog[open]")
    )
  );
}

function pendingCountLabel(count) {
  return `${count} ${t(count === 1 ? "pendingRequestSingular" : "pendingRequestPlural")}`;
}

function updatePendingNavigationCount(count) {
  const navItem = document.querySelector('[data-parent-nav="home"]');
  const badges = [...document.querySelectorAll("[data-parent-home-badge]")];
  if (!badges.length && navItem) {
    const badge = document.createElement("strong");
    badge.className = "nav-count";
    badge.dataset.parentHomeBadge = "";
    (navItem.querySelector(".parent-nav-icon") || navItem).append(badge);
    badges.push(badge);
  }
  badges.forEach(badge => {
    badge.textContent = String(count);
    badge.hidden = count === 0;
    badge.setAttribute("aria-label", pendingCountLabel(count));
  });
}

function setParentRefreshStatus(message = "", showButton = false) {
  if (!parentRefreshMessage) return;
  parentRefreshMessage.textContent = message;
  if (applyPendingRefreshButton) applyPendingRefreshButton.hidden = !showButton;
}

function announceNewParentRequest() {
  setParentRefreshStatus(t("newRequestReceived"), Boolean(deferredPendingHtml));
  window.setTimeout(() => {
    if (!deferredPendingHtml) setParentRefreshStatus();
  }, 5000);
}

function deferPendingReplacement(html) {
  deferredPendingHtml = html;
  setParentRefreshStatus(t("refreshRequests"), true);
}

function parsePendingReplacement(html) {
  return new DOMParser()
    .parseFromString(html, "text/html")
    .querySelector("[data-pending-requests-fragment]");
}

function applyPendingReplacement({allowFragmentFocus = false} = {}) {
  if (!deferredPendingHtml) return false;
  const fragment = currentPendingFragment();
  if (!fragment) return false;
  const activeElement = document.activeElement;
  if (!allowFragmentFocus && pendingRequestsHaveActiveInteraction(fragment)) return false;
  if (allowFragmentFocus && fragment.querySelector("dialog[open]")) return false;
  const focusTarget = allowFragmentFocus ? activeElement?.dataset?.openDialog : "";
  const replacement = parsePendingReplacement(deferredPendingHtml);
  if (!replacement) {
    deferredPendingHtml = "";
    return false;
  }
  fragment.replaceWith(replacement);
  deferredPendingHtml = "";
  setParentRefreshStatus();
  if (focusTarget) {
    [...replacement.querySelectorAll("[data-open-dialog]")]
      .find(element => element.dataset.openDialog === focusTarget)
      ?.focus();
  }
  return true;
}

function maybeApplyDeferredPendingReplacement() {
  if (!pendingRequestsHaveActiveInteraction(currentPendingFragment())) applyPendingReplacement();
}

function applyDeferredPendingAfterDialogClose(event) {
  window.setTimeout(() => {
    const closedDialog = event.target;
    const fragment = currentPendingFragment();
    if (
      closedDialog?.matches?.("dialog") &&
      fragment?.contains(closedDialog) &&
      !fragment.querySelector("dialog[open]")
    ) {
      applyPendingReplacement({allowFragmentFocus: true});
    } else {
      maybeApplyDeferredPendingReplacement();
    }
  }, 0);
}

function handleParentState(state) {
  const count = Number(state.count || 0);
  const revision = state.revision || "";
  const previousRevision = parentStateRevision;
  const previousCount = parentStateCount;
  const changed = Boolean(revision && revision !== previousRevision);
  parentStateRevision = revision || parentStateRevision;
  parentStateCount = count;
  updatePendingNavigationCount(count);
  if (!changed) {
    maybeApplyDeferredPendingReplacement();
    return;
  }
  if (previousRevision && count > previousCount) announceNewParentRequest();
  if (!state.html) return;
  const fragment = currentPendingFragment();
  if (!fragment || pendingRequestsHaveActiveInteraction(fragment)) {
    deferPendingReplacement(state.html);
    return;
  }
  const replacement = parsePendingReplacement(state.html);
  if (!replacement) return;
  fragment.replaceWith(replacement);
  setParentRefreshStatus();
}

function stopParentRefresh() {
  parentStateStopped = true;
  if (parentStateTimer !== null) window.clearTimeout(parentStateTimer);
  parentStateTimer = null;
  parentStateRequestController?.abort();
}

function scheduleParentStateCheck(delay = REFRESH_INTERVAL_MS) {
  if (!parentStateUrl || parentStateStopped || document.visibilityState !== "visible") return;
  if (parentStateTimer !== null) window.clearTimeout(parentStateTimer);
  parentStateTimer = window.setTimeout(() => {
    parentStateTimer = null;
    checkParentState();
  }, delay);
}

function forceParentStateCheck() {
  if (!parentStateUrl || parentStateStopped || document.visibilityState !== "visible") return;
  if (parentStateRequestRunning) {
    parentStateForcePending = true;
    parentStateRequestController?.abort();
    return;
  }
  scheduleParentStateCheck(0);
}

async function checkParentState() {
  if (
    !parentStateUrl ||
    parentStateStopped ||
    document.visibilityState !== "visible" ||
    parentStateRequestRunning
  ) return;
  parentStateRequestRunning = true;
  const controller = new AbortController();
  parentStateRequestController = controller;
  const timeout = window.setTimeout(() => controller.abort(), REFRESH_REQUEST_TIMEOUT_MS);
  try {
    const headers = { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" };
    if (parentStateRevision) headers["If-None-Match"] = `"${parentStateRevision}"`;
    const response = await fetch(parentStateUrl, {
      credentials: "same-origin",
      cache: "no-store",
      headers,
      signal: controller.signal,
    });
    if (
      response.redirected ||
      response.status === 401 ||
      response.status === 403 ||
      (response.status !== 304 && !response.headers.get("content-type")?.includes("application/json"))
    ) {
      stopParentRefresh();
      return;
    }
    if (response.status === 304) {
      parentStateFailures = 0;
      maybeApplyDeferredPendingReplacement();
      return;
    }
    if (!response.ok) throw new Error(`Parent state request failed: ${response.status}`);
    const state = await response.json();
    parentStateFailures = 0;
    handleParentState(state);
  } catch (error) {
    if (error.name !== "AbortError") parentStateFailures += 1;
  } finally {
    window.clearTimeout(timeout);
    if (parentStateRequestController === controller) parentStateRequestController = null;
    parentStateRequestRunning = false;
    if (parentStateForcePending && !parentStateStopped) {
      parentStateForcePending = false;
      scheduleParentStateCheck(0);
    } else {
      scheduleParentStateCheck(refreshBackoffDelay(parentStateFailures));
    }
  }
}

if (parentStateUrl) {
  applyPendingRefreshButton?.addEventListener("click", applyPendingReplacement);
  document.addEventListener("close", applyDeferredPendingAfterDialogClose, true);
  document.addEventListener("focusin", maybeApplyDeferredPendingReplacement);
  document.addEventListener("focusout", () => window.setTimeout(maybeApplyDeferredPendingReplacement, 0));
  document.addEventListener("pointerup", () => window.setTimeout(maybeApplyDeferredPendingReplacement, 0));
  document.addEventListener("keyup", () => window.setTimeout(maybeApplyDeferredPendingReplacement, 0));
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") forceParentStateCheck();
    else if (parentStateTimer !== null) {
      window.clearTimeout(parentStateTimer);
      parentStateTimer = null;
    }
  });
  window.addEventListener("focus", forceParentStateCheck);
  window.addEventListener("pageshow", forceParentStateCheck);
  window.addEventListener("online", forceParentStateCheck);
  window.addEventListener("pagehide", () => parentStateRequestController?.abort());
  window.addEventListener("beforeunload", () => parentStateRequestController?.abort());
  navigator.serviceWorker?.addEventListener("message", event => {
    if (event.data?.type === STATE_CHANGED_MESSAGE) forceParentStateCheck();
  });
  scheduleParentStateCheck();
}

function escapeBackupText(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadBackupStatus() {
  const section = document.querySelector("[data-backup-section]");
  if (!section) return;
  const statusUrl = section.dataset.backupStatusUrl;
  if (!statusUrl) return;
  try {
    const response = await fetch(statusUrl, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
    });
    if (!response.ok || !response.headers.get("content-type")?.includes("application/json")) {
      return;
    }
    const status = await response.json();
    const summary = section.querySelector("[data-backup-summary]");
    const summaryLabel = section.querySelector("[data-backup-summary-label]");
    const details = section.querySelector("[data-backup-details]");
    const runForm = section.querySelector("[data-backup-run-form]");
    const runButton = section.querySelector("[data-backup-run-button]");
    if (summary) {
      summary.className = `service-status settings-summary-status ${status.summary_class}`;
    }
    if (summaryLabel) summaryLabel.textContent = status.summary_label;
    if (details) {
      if (status.unavailable_message) {
        details.innerHTML = `<p class="danger-warning backup-warning">${escapeBackupText(status.unavailable_message)}</p>`;
      } else {
        const provider = escapeBackupText(status.provider || "—");
        const target = escapeBackupText(status.target || "—");
        const lastSuccess = escapeBackupText(status.last_success_display);
        const lastCheck = escapeBackupText(status.last_check_display);
        const error = status.error
          ? `<p class="danger-warning backup-warning">${escapeBackupText(status.error)}</p>`
          : "";
        details.innerHTML = `
          <dl class="service-details">
            <div><dt>${escapeBackupText(section.dataset.labelProvider)}</dt><dd>${provider}</dd></div>
            <div><dt>${escapeBackupText(section.dataset.labelRepository)}</dt><dd>${target}</dd></div>
            <div><dt>${escapeBackupText(section.dataset.labelLastSuccess)}</dt><dd>${lastSuccess}</dd></div>
            <div><dt>${escapeBackupText(section.dataset.labelLastCheck)}</dt><dd>${lastCheck}</dd></div>
          </dl>
          ${error}
        `;
      }
    }
    if (runForm) {
      runForm.hidden = !status.can_run;
      if (runButton) runButton.disabled = Boolean(status.running);
    }
  } catch (_error) {
    // Keep the checking placeholder if the backup agent is unreachable.
  }
}

loadBackupStatus();

function syncAssignmentPresetCadence(root) {
  const selected = root.querySelector("[data-preset-cadence]:checked");
  if (!selected) return;
  const cadence = selected.value;
  root.querySelectorAll("[data-preset-cadence-panel]").forEach((panel) => {
    const active = panel.dataset.presetCadencePanel === cadence;
    panel.hidden = !active;
    panel.querySelectorAll("input, select, textarea, button").forEach((field) => {
      field.disabled = !active;
    });
  });
}

document.querySelectorAll("[data-assignment-preset-save]").forEach((root) => {
  const radios = root.querySelectorAll("[data-preset-cadence]");
  if (radios.length) {
    syncAssignmentPresetCadence(root);
    radios.forEach((radio) => {
      radio.addEventListener("change", () => syncAssignmentPresetCadence(root));
    });
  }
  const saveButton = root.querySelector("[data-save-assignment-preset]");
  root.querySelectorAll("input, select").forEach((field) => {
    field.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      // Keep Enter inside Save-as-a-set from submitting Send tasks (first
      // type=submit in the shared Assign form).
      event.preventDefault();
      if (field instanceof HTMLInputElement && field.type === "radio") return;
      saveButton?.click();
    });
  });
});

document.querySelectorAll("[data-child-settings-accordion]").forEach((root) => {
  root.querySelectorAll("details.child-settings-acc").forEach((detail) => {
    detail.addEventListener("toggle", () => {
      if (!detail.open) return;
      root.querySelectorAll("details.child-settings-acc").forEach((other) => {
        if (other !== detail) other.open = false;
      });
    });
  });
});

const openChildSettingsFromHash = () => {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return;
  const target = document.getElementById(hash);
  if (target?.matches?.("details.child-settings-acc")) {
    const root = target.closest("[data-child-settings-accordion]");
    root?.querySelectorAll("details.child-settings-acc").forEach((detail) => {
      detail.open = detail === target;
    });
    window.requestAnimationFrame(() => {
      target.scrollIntoView({ block: "start" });
    });
    return;
  }
  if (hash === "nustatymai") {
    document.getElementById("nustatymai")?.scrollIntoView({ block: "start" });
  }
};
openChildSettingsFromHash();
window.addEventListener("hashchange", openChildSettingsFromHash);

document.querySelectorAll("[data-pin-change]").forEach((box) => {
  const form = box.querySelector("[data-pin-form]");
  if (!form) return;
  const steps = [...box.querySelectorAll("[data-pin-step]")];
  const stepTexts = steps.map(
    (el) => el.querySelector("[data-pin-step-text]")?.textContent?.trim() || ""
  );
  const label = box.querySelector("[data-pin-step-label]");
  const dots = [...box.querySelectorAll("[data-pin-dots] span")];
  const saveRow = box.querySelector("[data-pin-save]");
  const fields = {
    current_pin: form.querySelector('[data-pin-field="current_pin"]'),
    new_pin: form.querySelector('[data-pin-field="new_pin"]'),
    confirm_pin: form.querySelector('[data-pin-field="confirm_pin"]'),
  };
  const mismatchText = form.dataset.pinMismatch || "";
  const readyText = form.dataset.pinReady || "";
  let step = 0;
  let buffer = "";
  const values = ["", "", ""];

  const syncFields = () => {
    if (fields.current_pin) fields.current_pin.value = values[0];
    if (fields.new_pin) fields.new_pin.value = values[1];
    if (fields.confirm_pin) fields.confirm_pin.value = values[2];
  };

  const paint = () => {
    steps.forEach((el, i) => {
      el.classList.toggle("is-active", i === step && step < 3);
      el.classList.toggle("is-done", i < step || step >= 3);
      const num = el.querySelector(".step-num");
      if (num) num.textContent = i < step || step >= 3 ? "✓" : String(i + 1);
    });
    if (label) {
      if (step >= 3) label.textContent = readyText || stepTexts[2] || "";
      else label.textContent = stepTexts[step] || "";
    }
    dots.forEach((dot, i) => dot.classList.toggle("filled", i < buffer.length));
    const ready = step >= 3 && values[1] && values[1] === values[2];
    if (saveRow) saveRow.hidden = !ready;
    syncFields();
  };

  const advance = () => {
    values[step] = buffer;
    buffer = "";
    step += 1;
    if (step === 3 && values[1] !== values[2]) {
      step = 1;
      values[1] = "";
      values[2] = "";
      form.classList.add("is-pin-mismatch");
      window.setTimeout(() => form.classList.remove("is-pin-mismatch"), 420);
      if (label) label.textContent = mismatchText || stepTexts[1] || "";
      paint();
      return;
    }
    paint();
  };

  box.querySelector("[data-pin-pad]")?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-pin-key]");
    if (!button || step >= 3) return;
    const key = button.dataset.pinKey;
    if (key === "back") buffer = buffer.slice(0, -1);
    else if (/^\d$/.test(key) && buffer.length < 4) buffer += key;
    paint();
    if (buffer.length === 4) window.setTimeout(advance, 160);
  });

  form.addEventListener("submit", (event) => {
    syncFields();
    if (!(values[0] && values[1] && values[1] === values[2])) {
      event.preventDefault();
    }
  });

  paint();
});
