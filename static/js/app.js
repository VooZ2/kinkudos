const t = key => window.KINKUDOS?.i18n?.[key] || key;

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
document.querySelectorAll("[data-close-dialog]").forEach(button => {
  button.addEventListener("click", () => button.closest("dialog")?.close());
});
document.querySelectorAll("[data-open-dialog]").forEach(button => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.openDialog)?.showModal();
  });
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
document.querySelectorAll("[data-evidence-full]").forEach(button => {
  button.addEventListener("click", () => {
    const image = lightbox?.querySelector("[data-lightbox-image]");
    if (!image) return;
    image.src = button.dataset.evidenceFull;
    lightbox.showModal();
  });
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
  const openManageSection = id => {
    const sectionId = manageSectionForHash(id);
    if (!sectionId) return false;
    const target = document.getElementById(sectionId);
    if (!target) return false;
    parentShell.querySelectorAll(".catalog-grid > details").forEach(section => {
      section.open = section === target;
    });
    window.requestAnimationFrame(() => target.scrollIntoView({ behavior: "auto", block: "start" }));
    return true;
  };
  const showRoute = id => {
    showPanel(id);
    return openManageSection(id);
  };
  links.forEach(link => link.addEventListener("click", event => {
    event.preventDefault();
    const id = link.hash.slice(1);
    window.history.replaceState(window.history.state, "", `#${id}`);
    showPanel(id);
    scrollWorkspaceToTop();
  }));
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
    document.querySelector('[data-parent-nav="catalogs"]')?.click();
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
    url.hash = "parent-history";
    window.location.assign(url.toString());
  });
});

document.querySelector("[data-history-reset]")?.addEventListener("click", event => {
  const form = event.currentTarget.closest("form");
  if (!form) return;
  form.querySelector("[name=history_child]").value = "";
  form.querySelector("[name=history_activity]").value = "";
  form.querySelector("[name=history_date]").value = "week";
  form.querySelector("[name=history_start]").value = "";
  form.querySelector("[name=history_end]").value = "";
});

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
  const values = [...lotteryDialog.querySelectorAll("[data-lottery-value]")];
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

document.querySelectorAll("[data-toggle-edit]").forEach(button => {
  button.addEventListener("click", () => {
    const form = document.getElementById(`edit-${button.dataset.toggleEdit}`);
    if (!form) return;
    form.hidden = !form.hidden;
    button.setAttribute("aria-expanded", String(!form.hidden));
    if (!form.hidden) form.querySelector("input")?.focus();
  });
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
    after.textContent = String(Math.min(saved + amount, target));
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

const childStateUrl = window.KINKUDOS?.childStateUrl;
let childStateSignature = window.KINKUDOS?.childStateSignature || "";
let childRefreshDeferred = false;
let childStateRequestRunning = false;

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

async function checkChildState() {
  if (!childStateUrl || document.visibilityState !== "visible" || childStateRequestRunning) return;
  childStateRequestRunning = true;
  try {
    const response = await fetch(childStateUrl, {
      credentials: "same-origin",
      cache: "no-store",
      headers: { Accept: "application/json" }
    });
    if (!response.ok) return;
    const state = await response.json();
    if (!childStateSignature) {
      childStateSignature = state.signature;
    } else if (state.signature && state.signature !== childStateSignature) {
      childStateSignature = state.signature;
      reloadChildPageWhenSafe();
    }
  } catch (_) {
    // A temporary connection problem should not interrupt the child.
  } finally {
    childStateRequestRunning = false;
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
      window.location.reload();
    }
  }, true);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") checkChildState();
  });
  window.addEventListener("focus", checkChildState);
  navigator.serviceWorker?.addEventListener("message", event => {
    if (event.data?.type === "kinkudos-state-changed") checkChildState();
  });
  window.setInterval(checkChildState, 15000);
}
