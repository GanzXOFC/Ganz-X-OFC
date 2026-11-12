(() => {
  const guestKey = "gx_chat_guest_token";
  const guestBox = document.getElementById("gx-chat-guest-box");
  const guestName = document.getElementById("gx-chat-guest-name");
  const startButton = document.getElementById("gx-chat-start");
  const chatArea = document.getElementById("gx-chat-area");
  const pushButton = document.getElementById("gx-chat-push-enable");
  const messagesBox = document.getElementById("gx-chat-messages");
  const form = document.getElementById("gx-chat-form");
  const input = document.getElementById("gx-chat-input");
  const photoInput = document.getElementById("gx-chat-photo");
  const photoButton = document.getElementById("gx-chat-photo-button");
  const photoPreview = document.getElementById("gx-chat-photo-preview");
  const photoThumb = document.getElementById("gx-chat-photo-thumb");
  const photoCancel = document.getElementById("gx-chat-photo-cancel");
  let selectedPhoto = null;
  let previewUrl = "";

  function showPhotoViewer(blob, filename) {
    const url = URL.createObjectURL(blob);

    const overlay = document.createElement("div");
    overlay.style.cssText = "position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.94);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:14px;";

    const bar = document.createElement("div");
    bar.style.cssText = "width:100%;max-width:600px;display:flex;justify-content:flex-end;gap:10px;margin-bottom:12px;";

    const save = document.createElement("a");
    save.textContent = "SIMPAN";
    save.href = url;
    save.download = filename + ".jpg";
    save.style.cssText = "background:#1769ff;color:white;padding:11px 16px;border-radius:9px;text-decoration:none;font-weight:bold;font-size:13px;";


    const large = document.createElement("img");
    large.src = url;
    large.alt = "Foto chat";
    large.style.cssText = "max-width:100%;max-height:82vh;object-fit:contain;border-radius:10px;";

    function removeViewer() {
      URL.revokeObjectURL(url);
      overlay.remove();
    }

    overlay.addEventListener("click", e => {
      if (e.target === overlay) removeViewer();
    });

    bar.append(save);
    overlay.append(bar, large);
    document.body.appendChild(overlay);
  }

  const errorBox = document.getElementById("gx-chat-error");

  if (!guestBox || !chatArea || !form) return;

  let conversationReady = false;
  let loading = false;
  let polling = null;
  let lastMessageId = 0;
  let adminOnline = false;
  let customerOnline = false;
  const messageNodes = new Map();

  function updateMessageMeta(entry) {
    const {meta, item} = entry;
    const time = meta.querySelector(".gx-chat-time");
    const ticks = meta.querySelector(".gx-chat-ticks");

    time.textContent = item.created_time || "";

    if (item.sender !== "customer") {
      ticks.textContent = "";
      ticks.style.display = "none";
      return;
    }

    ticks.style.display = "inline-block";

    ticks.innerHTML = item.read_at
      ? "&#10003;&#10003;"
      : (adminOnline ? "&#10003;&#10003;" : "&#10003;");

    ticks.style.color = item.read_at
      ? "#53bdeb"
      : "#c7d2d8";
  }

  function updateAllMessageMeta() {
    for (const entry of messageNodes.values()) {
      updateMessageMeta(entry);
    }
  }

  function accountToken() {
    try {
      return localStorage.getItem("gx_account_token") || "";
    } catch (_) {
      return "";
    }
  }

  function guestToken() {
    try {
      return localStorage.getItem(guestKey) || "";
    } catch (_) {
      return "";
    }
  }

  function headers() {
    const h = {};
    const account = accountToken();
    const guest = guestToken();

    if (account) h["X-Account-Token"] = account;
    else if (guest) h["X-Chat-Guest-Token"] = guest;

    return h;
  }

  function showError(message) {
    errorBox.textContent = message || "";
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers(),
        ...(options.headers || {})
      }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || data.ok === false) {
      throw new Error(data.message || "Permintaan gagal.");
    }

    return data;
  }

  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    const raw = atob(base64);
    return Uint8Array.from(raw, char => char.charCodeAt(0));
  }


  function addMessage(item) {
    if (!item || !item.id) return;

    const existing = messageNodes.get(String(item.id));
    if (existing) {
      existing.item = item;
      updateMessageMeta(existing);
      return;
    }

    const bubble = document.createElement("div");
    bubble.style.cssText = [
      "max-width:85%",
      "padding:10px 12px",
      "border-radius:12px",
      "font-size:13px",
      "line-height:1.5",
      "white-space:pre-wrap",
      "overflow-wrap:anywhere",
      item.sender === "customer"
        ? "align-self:flex-end;background:#075e54;color:white"
        : "align-self:flex-start;background:#211a32;color:#eee"
    ].join(";");

    const label = document.createElement("div");
    label.textContent = item.sender === "customer" ? "anda" : "Caca";
    label.style.cssText = "font-size:10px;font-weight:900;margin-bottom:4px";

    if (item.sender === "customer") {
      const profileName = document.querySelector(".profile-header .profile-name");
      const nameColor = profileName?.dataset.nameColor || "white";

      const colors = {
        white: "#ffffff",
        red: "#ff4242",
        blue: "#398cff"
      };

      if (nameColor === "gradient") {
        label.style.background = "linear-gradient(90deg,#42a5ff,#4d75ff,#9870ff,#c16bff,#6b8cff)";
        label.style.webkitBackgroundClip = "text";
        label.style.backgroundClip = "text";
        label.style.color = "transparent";
        label.style.webkitTextFillColor = "transparent";
      } else {
        label.style.color = colors[nameColor] || colors.white;
      }
    } else {
      label.style.background = "linear-gradient(90deg,#42a5ff,#4d75ff,#9870ff,#c16bff,#6b8cff)";
      label.style.webkitBackgroundClip = "text";
      label.style.backgroundClip = "text";
      label.style.color = "transparent";
      label.style.webkitTextFillColor = "transparent";
    }

    const content = document.createElement("div");

    if (item.has_photo) {
      const image = document.createElement("img");
      image.alt = "Foto dari chat";
      image.style.cssText = "display:block;max-width:100%;max-height:260px;object-fit:contain;border-radius:9px;margin-top:4px;";
      content.appendChild(image);

      fetch("/api/chat/photo/" + item.id, {headers: headers()})
        .then(response => {
          if (!response.ok) throw new Error("Foto gagal dimuat.");
          return response.blob();
        })
        .then(blob => {
          image.src = URL.createObjectURL(blob);
          image.style.cursor = "zoom-in";
          image.addEventListener("click", () => showPhotoViewer(blob, "foto-chat-" + item.id));
        })
        .catch(() => {
          content.textContent = "Foto tidak dapat dimuat.";
        });
    } else {
      content.textContent = item.message;
    }

    const meta = document.createElement("div");
    meta.style.cssText = "display:flex !important;visibility:visible !important;justify-content:flex-end;align-items:center;gap:5px;font-size:11px;line-height:1.2;margin-top:7px;opacity:1;min-height:13px;width:100%;";

    const time = document.createElement("span");
    time.className = "gx-chat-time";

    const ticks = document.createElement("span");
    ticks.className = "gx-chat-ticks";
    ticks.style.cssText = "display:inline-block !important;visibility:visible !important;font-weight:900;font-size:13px;min-width:16px;text-align:right;color:#c7d2d8;";

    meta.append(time, ticks);
    bubble.append(label, content, meta);
    messagesBox.appendChild(bubble);

    const entry = {meta, item};
    messageNodes.set(String(item.id), entry);
    updateMessageMeta(entry);

    lastMessageId = Math.max(lastMessageId, Number(item.id));
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  async function loadMessages() {
    if (!conversationReady || loading) return;
    loading = true;

    try {
      const data = await request("/api/chat/messages");
      adminOnline = !!data.admin_online;
      customerOnline = true;

      for (const item of data.messages || []) {
        addMessage(item);
      }

      updateAllMessageMeta();

      if (
        document.visibilityState === "visible" &&
        chatArea &&
        chatArea.style.display !== "none"
      ) {
        await request("/api/chat/read", {method: "POST"});
      }

      showError("");
    } catch (error) {
      showError(error.message);
    } finally {
      loading = false;
    }
  }

  async function openChat(name = "") {
    showError("");
    const loadingBox = document.getElementById("gx-chat-loading");
    loadingBox.style.display = "block";

    try {
      const data = await request("/api/chat/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(name ? { guest_name: name } : {})
      });

      if (data.guest && data.guest_token) {
        localStorage.setItem(guestKey, data.guest_token);
      }

      conversationReady = true;
      guestBox.style.display = "none";
      chatArea.style.display = "block";

      await loadMessages();
      await restorePushSubscription();

      if (polling) clearInterval(polling);
      polling = setInterval(loadMessages, 4000);
    } catch (error) {
      showError(error.message);
    } finally {
      loadingBox.style.display = "none";
    }
  }

  async function restorePushSubscription() {
    if (!pushButton) return;

    pushButton.disabled = false;
    pushButton.style.display = "";

    if (!("serviceWorker" in navigator) ||
        !("PushManager" in window) ||
        !("Notification" in window) ||
        Notification.permission !== "granted") return;

    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();
      if (!subscription) return;

      await request("/api/chat/push/subscribe", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({subscription: subscription.toJSON()})
      });

      pushButton.style.display = "none";
    } catch (error) {
      console.warn("Gagal memulihkan langganan push:", error);
    }
  }

  if (pushButton) {
    pushButton.addEventListener("click", async () => {
      if (!conversationReady) {
        showError("Buka chat terlebih dahulu.");
        return;
      }

      if (!("serviceWorker" in navigator) ||
          !("PushManager" in window) ||
          !("Notification" in window)) {
        showError("Browser ini belum mendukung notifikasi push.");
        return;
      }

      pushButton.disabled = true;
      showError("");

      try {
        let permission = Notification.permission;
        if (permission === "default") {
          permission = await Notification.requestPermission();
        }
        if (permission !== "granted") {
          throw new Error("Izin notifikasi belum diberikan.");
        }

        const registration = await navigator.serviceWorker.ready;
        let subscription = await registration.pushManager.getSubscription();

        const keyData = await request("/api/chat/push/public-key");
        if (!subscription) {
          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(keyData.public_key)
          });
        }

        await request("/api/chat/push/subscribe", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({subscription: subscription.toJSON()})
        });

        pushButton.style.display = "none";
        showError("Notifikasi chat berhasil diaktifkan.");
      } catch (error) {
        showError(error.message || "Gagal mengaktifkan notifikasi.");
      } finally {
        pushButton.disabled = false;
      }
    });
  }

  window.gxChatOpen = async function () {
    if (conversationReady) {
      await loadMessages();
      return;
    }

    if (accountToken() || guestToken()) {
      await openChat();
    } else {
      guestBox.style.display = "block";
      chatArea.style.display = "none";
      guestName.focus();
    }
  };

  startButton.addEventListener("click", async () => {
    const name = guestName.value.trim();

    if (name.length < 2 || name.length > 30) {
      showError("Nama harus 2–30 karakter.");
      return;
    }

    startButton.disabled = true;
    await openChat(name);
    startButton.disabled = false;
  });

  function clearPhoto() {
    selectedPhoto = null;
    photoInput.value = "";
    photoPreview.style.display = "none";
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = "";
    photoThumb.removeAttribute("src");
  }

  photoButton.addEventListener("click", () => photoInput.click());

  photoInput.addEventListener("change", () => {
    const file = photoInput.files && photoInput.files[0];
    if (!file) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      showError("Pilih foto JPEG, PNG, atau WEBP.");
      clearPhoto();
      return;
    }
    if (file.size > 3 * 1024 * 1024) {
      showError("Ukuran foto maksimal 3 MB.");
      clearPhoto();
      return;
    }

    selectedPhoto = file;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    photoThumb.src = previewUrl;
    photoPreview.style.display = "flex";
    showError("");
  });

  photoCancel.addEventListener("click", clearPhoto);

  form.addEventListener("submit", async event => {
    event.preventDefault();

    const message = input.value.trim();
    if (!selectedPhoto && (!message || message.length > 1000)) return;

    const sendButton = form.querySelector('button[type="submit"]');
    sendButton.disabled = true;
    photoButton.disabled = true;

    try {
      if (selectedPhoto) {
        const formData = new FormData();
        formData.append("photo", selectedPhoto);
        await request("/api/chat/photo", {
          method: "POST",
          body: formData
        });
        clearPhoto();
      } else {
        await request("/api/chat/messages", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({message})
        });
        input.value = "";
      }

      await loadMessages();
      showError("");
    } catch (error) {
      showError(error.message);
    } finally {
      sendButton.disabled = false;
      photoButton.disabled = false;
    }
  });

  window.addEventListener("beforeunload", () => {
    if (polling) clearInterval(polling);
  });
})();
