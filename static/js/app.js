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
  const showPanel = id => {
    if (!panels.some(panel => panel.id === id)) id = panels[0]?.id;
    panels.forEach(panel => { panel.hidden = panel.id !== id; });
    links.forEach(link => {
      const active = link.getAttribute("href") === `#${id}`;
      link.classList.toggle("is-active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  };
  links.forEach(link => link.addEventListener("click", event => {
    event.preventDefault();
    const id = link.hash.slice(1);
    window.history.replaceState(window.history.state, "", `#${id}`);
    showPanel(id);
    scrollWorkspaceToTop();
  }));
  showPanel(window.location.hash.slice(1) || panels[0]?.id);
  if (window.location.hash) scrollWorkspaceToTop();
  window.addEventListener("hashchange", () => {
    showPanel(window.location.hash.slice(1));
    scrollWorkspaceToTop();
  });
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
  iconUse?.setAttribute("href", muted ? "#icon-sound-off" : "#icon-sound-on");
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

function urlBase64ToUint8Array(value) {
  const padding = "=".repeat((4 - value.length % 4) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(base64), char => char.charCodeAt(0));
}

const pushButton = document.getElementById("enable-push");
const pushHelpDialog = document.getElementById("push-help-dialog");
const pushHelpText = pushHelpDialog?.querySelector("[data-push-help-text]");
const t = key => window.KINKUDOS?.i18n?.[key] || key;

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
      .register("/service-worker.js")
      .then(() => refreshPushState())
      .catch(() => setPushState("unsupported", t("notificationsUnsupported")));
  });
} else {
  setPushState("unsupported", t("notificationsUnsupported"));
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
