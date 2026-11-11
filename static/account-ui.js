(() => {
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  let token = localStorage.getItem("gx_account_token") || "";
  let account = null;
  let mode = "login";

  const style = document.createElement("style");
  style.textContent = `
  #gx-account-btn{display:none!important;position:static;right:auto;top:auto;z-index:10;border:1px solid #7562ff;
  border-radius:12px;padding:9px 12px;background:#17132b;color:#fff;font-weight:bold}
  #gx-account-modal{position:fixed;inset:0;z-index:99999;background:#05030de8;display:none;
  align-items:center;justify-content:center;padding:18px;font-family:Arial,sans-serif}
  #gx-account-card{width:min(360px,100%);background:#171326;border:1px solid #8066ff;
  border-radius:18px;padding:20px;color:white;box-sizing:border-box}
  #gx-account-card h2{text-align:center;color:#c6b6ff}
  #gx-account-card input,#gx-account-card select{width:100%;box-sizing:border-box;padding:12px;
  margin:6px 0;border-radius:10px;border:1px solid #5c4a83;background:#0c0917;color:white}
  #gx-account-card button{width:100%;padding:12px;margin-top:8px;border:0;border-radius:10px;
  background:linear-gradient(90deg,#694cff,#bd54ff);color:white;font-weight:bold}
  #gx-account-card .gx-secondary{background:#302747}
  #gx-password-wrap{position:relative;width:100%}
  #gx-password-wrap input{padding-right:52px!important}
  #gx-password-wrap button{
    position:absolute;right:5px;top:50%;transform:translateY(-50%);
    width:40px;height:38px;padding:0;margin:0;background:transparent;
    color:white;font-size:19px;border:0;cursor:pointer
  }
  #gx-account-msg{font-size:13px;white-space:pre-wrap;margin-top:10px;color:#ffe1f4}
  `;
  document.head.appendChild(style);

  const modal = document.createElement("div");
  modal.id = "gx-account-modal";
  modal.innerHTML = `
    <div id="gx-account-card">
      <div style="display:flex;align-items:center;gap:12px"><button id="gx-auth-close" type="button" aria-label="Kembali" style="flex:0 0 32px;width:32px;padding:0;margin:-18px 0 0;background:transparent;border:0;color:white;font-size:28px;cursor:pointer">←</button><h2 style="flex:1;margin:0;text-align:center;transform:translateX(-21px)">Ganz X - OFC</h2></div>
      <div id="gx-account-title"> AKUN</div>
      <input id="gx-username" placeholder="Username" maxlength="24" autocomplete="username">
      <div id="gx-password-wrap">
        <input id="gx-password" type="password" placeholder="Password" autocomplete="current-password">
        <button id="gx-password-toggle" type="button" aria-label="Lihat password">👁</button>
      </div>
      <button id="gx-auth-submit"></button>
      <button id="gx-auth-switch" class="gx-secondary">BELUM PUNYA AKUN? DAFTAR</button>

      <div id="gx-account-msg"></div>
    </div>`;
  document.body.appendChild(modal);
  const passwordInput = $("#gx-password");
  const passwordToggle = $("#gx-password-toggle");

  passwordToggle.addEventListener("click", () => {
    const visible = passwordInput.type === "password";
    passwordInput.type = visible ? "text" : "password";
    passwordToggle.setAttribute("aria-label", visible ? "Sembunyikan password" : "Lihat password");
  });


  const brandStyle = document.createElement('style'); brandStyle.textContent = '.gx-login-brand{display:block;background:linear-gradient(90deg,#1e5aa8,#7b2cff);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}.gx-login-label{display:block;color:#c6b6ff;-webkit-text-fill-color:#c6b6ff;font-size:12px;margin-top:4px}'; document.head.appendChild(brandStyle);
  const accountBtn = document.createElement("button");
  accountBtn.id = "gx-account-btn";
  accountBtn.textContent = "LOGIN";
  document.body.appendChild(accountBtn);

  function showModal(nextMode="login") {
    mode = nextMode;
    $("#gx-account-title").innerHTML = (mode === "login" ? '<small class="gx-login-label">LOGIN</small>' : '<small class="gx-login-label">BUAT AKUN</small>');
    $("#gx-auth-submit").textContent = mode === "login" ? "MASUK" : "BUAT AKUN";
    $("#gx-auth-switch").textContent = mode === "login" ? "BUAT AKUN" : "SUDAH PUNYA AKUN? ";
    $("#gx-account-msg").textContent = "";
    modal.style.display = "flex";
  }

  document.addEventListener("click", function(event) {
    const btn = event.target.closest("#gx-login-welcome-btn");
    if (btn) {
      event.preventDefault();
      showModal("login");
    }
  });
  function message(text) { $("#gx-account-msg").textContent = text; }

  async function api(path, body) {
    const headers = {"Content-Type":"application/json"};
    if (token) headers["X-Account-Token"] = token;
    const res = await fetch(path, {
      method: body ? "POST" : "GET",
      headers,
      ...(body ? {body:JSON.stringify(body)} : {})
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
    const err = new Error(data.error || data.message || `HTTP ${res.status}`);
    err.data = data;
    err.status = res.status;
    throw err;
  }
    return data;
  }

  function updateWelcomeLoginButton() {
    const btn = document.getElementById("gx-login-welcome-btn");
    if (btn) btn.style.display = token ? "none" : "block";
  }

  function updateAccount(data) {
    account = data.account || data.user || data;
    updateWelcomeLoginButton();
    const username = account.username || account.name || "AKUN";
    const displayName = account.display_name || "Ganz X - OFC";
    const headerName = document.querySelector(".profile-header .profile-name");
    if (headerName) {
      headerName.textContent = displayName;
      headerName.dataset.nameColor = account.name_color || "white";
    }
    const homeUsername = document.getElementById("gx-home-username");
    if (homeUsername) {
      homeUsername.textContent = "👤 " + username;
      homeUsername.style.display = "block";
    }
    const coins = account.coins ?? account.balance ?? data.coins ?? 0;
    accountBtn.textContent = `👤 ${username} · 🪙 ${coins}`;
    const oldCoin = $("#gx-coin-label");
    if (oldCoin) oldCoin.textContent = `🪙 COINS : ${coins}`;
    renderProfile();
  }


  function setProfileAvatar(url) {
    const image = url || "/static/profil.webp";
    const profileImage = document.getElementById("gx-profile-avatar");
    const homeImage = document.querySelector(".profile-header .profile img");
    if (profileImage) profileImage.src = image;
    if (homeImage) homeImage.src = image;
  }

  function renderProfile() {
    if (!account) return;
    const usernameBox = document.getElementById("gx-profile-username");
    const coinsBox = document.getElementById("gx-profile-coins");
    const displayNameInput = document.getElementById("gx-display-name");
    const headerName = document.querySelector(".profile-header .profile-name");
    const displayName = account.display_name || "Ganz X - OFC";
    if (displayNameInput && document.activeElement !== displayNameInput) displayNameInput.value = displayName;
    if (headerName) {
      headerName.textContent = displayName;
      headerName.dataset.nameColor = account.name_color || "white";
    }
    renderNameColorControls();
    renderCrownControls();
    const crownVisible = !!account.crown_enabled;
    const homeCrown = document.getElementById("gx-home-crown");
    const accountCrown = document.getElementById("gx-account-crown");
    if (homeCrown) homeCrown.style.display = crownVisible ? "block" : "none";
    if (accountCrown) accountCrown.style.display = crownVisible ? "block" : "none";
    if (usernameBox) usernameBox.textContent = account.username || "AKUN";
    if (coinsBox) coinsBox.textContent = "🪙 " + (account.coins ?? 0);
    setProfileAvatar(account.avatar_url || "/static/profil.webp");
  }

  function renderNameColorControls() {
    const panel = document.getElementById("gx-name-color-panel");
    const progress = document.getElementById("gx-name-color-progress");
    const options = document.getElementById("gx-name-color-options");
    if (!panel || !progress || !options) return;

    if (!account) {
      progress.textContent = "Login untuk melihat progres warna.";
      options.innerHTML = "";
      return;
    }

    const spent = Number(account.total_spent || 0);
    const unlocked = ["white", ...(spent >= 20 ? ["red"] : []),
      ...(spent >= 50 ? ["blue"] : []), ...(spent >= 100 ? ["gradient"] : [])];
    const current = account.name_color || "white";
    progress.textContent = `Total Coins ${spent} / 100`;

    const choices = [
      {id:"white", label:"WHITE", cost:0, color:"#ffffff"},
      {id:"red", label:"RED", cost:20, color:"#ff4242"},
      {id:"blue", label:"BLUE", cost:50, color:"#4295ff"},
      {id:"gradient", label:"BLUE NEON", cost:100, color:"#b879ff"}
    ];

    options.innerHTML = choices.map(item => {
      const open = unlocked.includes(item.id);
      const selected = current === item.id;
      return `<button type="button" data-gx-name-color="${item.id}"
        ${open ? "" : "disabled"}
        style="width:100%;margin:0;padding:10px;border-radius:9px;border:1px solid ${selected ? item.color : "#514174"};
        background:${selected ? "#29203d" : "#171326"};color:${item.color};font-weight:900;opacity:${open ? "1" : ".48"};">
        ${item.id === "gradient"
          ? `<span style="background:linear-gradient(90deg,#00aaff,#397bff,#7655ff,#bd55ff);-webkit-background-clip:text;background-clip:text;color:transparent;-webkit-text-fill-color:transparent;">${item.label}</span>`
          : item.label}${selected ? "" : open ? "" : ` ${item.cost} COINS 🔒`}
      </button>`;
    }).join("");
  }

  function renderCrownControls() {
    const progress = document.getElementById("gx-crown-progress");
    const options = document.getElementById("gx-crown-options");
    if (!progress || !options) return;

    if (!account) {
      progress.textContent = "Login untuk melihat progres mahkota.";
      options.innerHTML = "";
      return;
    }

    const spent = Number(account.total_spent || 0);
    const unlocked = spent >= 500;
    const enabled = !!account.crown_enabled;

    progress.textContent = `Total Coins ${spent} / 500`;

    options.innerHTML = `<button type="button" id="gx-crown-toggle"
      ${unlocked ? "" : "disabled"}
      style="width:100%;padding:10px;border-radius:9px;border:1px solid ${enabled ? "#ffd700" : "#514174"};
      background:${enabled ? "#302716" : "#171326"};color:${unlocked ? "#ffd700" : "#c8b9e8"};
      font-weight:900;opacity:${unlocked ? "1" : ".48"};">
      ${!unlocked ? "500 COINS 🔒" : enabled ? "MATIKAN" : "AKTIFKAN"}
    </button>`;
  }

  document.getElementById("gx-crown-options")?.addEventListener("click", async event => {
    const button = event.target.closest("#gx-crown-toggle");
    if (!button || button.disabled) return;

    button.disabled = true;
    try {
      const result = await api("/api/account/crown", {
        enabled: !account.crown_enabled
      });
      account.crown_enabled = result.crown_enabled;
      account.total_spent = result.total_spent;
      renderProfile();

      const msg = document.getElementById("gx-profile-message");
      if (msg) msg.textContent = result.message;
    } catch (error) {
      const msg = document.getElementById("gx-profile-message");
      if (msg) msg.textContent = error.message || "Gagal mengubah mahkota.";
    } finally {
      button.disabled = false;
    }
  });

  document.getElementById("gx-name-color-options")?.addEventListener("click", async event => {
    const button = event.target.closest("[data-gx-name-color]");
    if (!button || button.disabled) return;
    button.disabled = true;
    try {
      const result = await api("/api/account/name-color", {
        color: button.dataset.gxNameColor
      });
      account.name_color = result.name_color;
      account.total_spent = result.total_spent;
      renderProfile();
    } catch (error) {
      const msg = document.getElementById("gx-profile-message");
      if (msg) msg.textContent = error.message || "Gagal mengganti warna.";
    } finally {
      button.disabled = false;
    }
  });

  function escapeHtml(value) {
    const el = document.createElement("span");
    el.textContent = String(value ?? "");
    return el.innerHTML;
  }

  async function loadTopCoins() {
    const list = document.getElementById("gx-topcoins-list");
    if (!list) return;
    list.textContent = "Memuat...";
    try {
      const response = await fetch("/api/leaderboard", {cache:"no-store"});
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error("Gagal memuat leaderboard.");
      if (!data.users || !data.users.length) {
        list.textContent = "Belum ada akun.";
        return;
      }
      list.innerHTML = data.users.map(user => `
        <div class="gx-topcoin-row">
          <div class="gx-topcoin-rank rank-${Number(user.rank)}">${Number(user.rank)}.</div>
          <div class="gx-topcoin-avatar">
            ${user.crown_enabled ? '<span class="gx-topcoin-crown" aria-hidden="true">👑</span>' : ''}
            <img src="${escapeHtml(user.avatar_url)}" alt="" loading="lazy" decoding="async" fetchpriority="low" onerror="this.src='/static/profil.webp'">
          </div>
          <div class="gx-topcoin-name" data-name-color="${["white","red","blue","gradient"].includes(user.name_color) ? user.name_color : "white"}">${escapeHtml(user.display_name || "Ganz X - OFC")}</div>
          <div class="gx-topcoin-balance">🪙 ${Number(user.coins).toLocaleString("id-ID")}</div>
        </div>
      `).join("");
    } catch (error) {
      list.textContent = error.message || "Koneksi gagal.";
    }
  }

  document.querySelector('[data-gx-page="account"]')?.addEventListener("click", event => {
    if (!token || !account) {
      event.preventDefault();
      event.stopImmediatePropagation();
      showModal("login");
      message("Login terlebih dahulu untuk membuka profil.");
      return;
    }
    renderProfile();
  }, true);

  document.querySelector('[data-gx-page="topcoins"]')?.addEventListener("click", loadTopCoins);
  document.getElementById("gx-topcoins-refresh")?.addEventListener("click", loadTopCoins);

  document.getElementById("gx-avatar-file")?.addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      $("#gx-profile-message").textContent = "Ukuran foto maksimal 5 MB.";
      event.target.value = "";
      return;
    }
    const form = new FormData();
    form.append("avatar", file);
    try {
      const response = await fetch("/api/account/avatar", {
        method:"POST",
        headers:{"X-Account-Token":token},
        body:form
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || "Upload foto gagal.");
      account.avatar_url = data.avatar_url;
      setProfileAvatar(data.avatar_url);
      $("#gx-profile-message").textContent = "Foto profil berhasil diperbarui";
    } catch (error) {
      $("#gx-profile-message").textContent = error.message;
    }
    event.target.value = "";
  });

  document.getElementById("gx-display-name-form")?.addEventListener("submit", async event => {
    event.preventDefault();
    const display_name = $("#gx-display-name").value.trim();
    try {
      const result = await api("/api/account/name", {display_name});
      account.display_name = result.display_name;
      renderProfile();
      $("#gx-profile-message").textContent = (result.message || "Nama berhasil disimpan").replace(/[.]+$/, "");
    } catch (error) {
      $("#gx-profile-message").textContent = error.message || "Gagal menyimpan nama.";
    }
  });

  document.getElementById("gx-password-form")?.addEventListener("submit", async event => {
    event.preventDefault();
    const current_password = $("#gx-current-password").value;
    const new_password = $("#gx-new-password").value;
    try {
      const result = await api("/api/account/password", {current_password,new_password});
      $("#gx-profile-message").textContent = result.message || "Password berhasil diganti.";
      event.target.reset();
    } catch (error) {
      $("#gx-profile-message").textContent = error.message;
    }
  });

  document.getElementById("gx-profile-logout")?.addEventListener("click", async () => {
    if (!confirm("Yakin ingin logout dari akun ini?")) return;
    try { await api("/api/logout", {}); } catch (_) {}
    token = "";
    account = null;
    localStorage.removeItem("gx_account_token");
    await refreshAccount();
    document.querySelector('[data-gx-page="home"]')?.click();
  });

  async function refreshAccount() {
    if (!token) {
      account = null;
      updateWelcomeLoginButton();
      accountBtn.textContent = "";
      const homeUsername = document.getElementById("gx-home-username");
      if (homeUsername) homeUsername.style.display = "none";
      setProfileAvatar("/static/profil.webp");
      const profileName = document.getElementById("gx-profile-username");
      const headerName = document.querySelector(".profile-header .profile-name");
      if (headerName) {
        headerName.dataset.nameColor = "white";
        headerName.textContent = "Ganz X - OFC";
      }
      renderNameColorControls();
      const profileCoins = document.getElementById("gx-profile-coins");
      if (profileName) profileName.textContent = "Belum login";
      if (profileCoins) profileCoins.textContent = "0";
      const oldCoin = $("#gx-coin-label");
      if (oldCoin) oldCoin.textContent = "🪙 COINS : 0";
      return;
    }
    try {
      updateAccount(await api("/api/account"));
    } catch (err) {
      if (err.status === 401) {
        token = "";
        localStorage.removeItem("gx_account_token");
        account = null;
        updateWelcomeLoginButton();
        accountBtn.textContent = "";
      } else {
        accountBtn.textContent = "👤 Akun tersimpan · koneksi terganggu";
      }
    }
  }

  const homeUsernameBtn = document.getElementById("gx-home-username");
  if (homeUsernameBtn) {
    homeUsernameBtn.style.cursor = "pointer";
    homeUsernameBtn.title = "Buka profil akun";
    homeUsernameBtn.addEventListener("click", () => {
      if (token && account) {
        document.querySelector('[data-gx-page="account"]')?.click();
      } else {
        showModal("login");
      }
    });
  }

  $("#gx-auth-close").onclick = () => modal.style.display = "none";
  $("#gx-auth-switch").style.display="block"; $("#gx-auth-switch").onclick = () => showModal(mode === "login" ? "register" : "login");

  $("#gx-auth-submit").onclick = async () => {
    const username = $("#gx-username").value.trim();
    const password = $("#gx-password").value;
    if (!username || !password) return message("Masukan username & password bebas");
    try {
      if (mode === "register") {
        await api("/api/register", {username,password});
        token = "";
        account = null;
        localStorage.removeItem("gx_account_token");
        await refreshAccount();
        $("#gx-username").value = username;
        $("#gx-password").value = "";
        showModal("login");
        message("akun berhasil di buat ✅\nsilahkan login dengan password yang baru di buat.");
        return;
      }

      const data = await api("/api/login", {username,password});
      token = data.token || data.account_token || data.session_token || "";
      if (!token) throw new Error("Token akun tidak diterima backend.");
      localStorage.setItem("gx_account_token", token);
      await refreshAccount();
      modal.style.display = "none";
      alert("Login berhasil!");
    } catch (e) { message(e.message); }
  };

  // Tangkap submit lebih awal agar handler lama tidak mengirim request ganda.
  document.addEventListener("submit", async event => {
    const form = event.target.closest(".gx-form");
    if (!form || !["free", "vip", "like20"].includes(form.dataset.service)) return;

    event.preventDefault();
    event.stopImmediatePropagation();

    const output = form.parentElement.querySelector(".gx-message");
    const button = form.querySelector('button[type="submit"]');
    const oldText = button?.textContent;

    function showResult(text) {
      if (!output) return;
      output.style.display = "block";
      output.style.whiteSpace = "pre-line";
      output.textContent = text;
    }

    if (!token) {
      showModal("login");
      showResult("Login terlebih dahulu sebelum mengirim LIKE.");
      return;
    }

    const uid = form.querySelector('[name="uid"]')?.value.trim();
    const region = form.querySelector('[name="region"]')?.value || "ID";
    const service = form.dataset.service;
    const cost = service === "vip" ? 5 : 1;
    if (!uid) {
      showResult("Masukkan UID Free Fire.");
      return;
    }

    await refreshAccount();

    if (!token || !account) {
      showResult("Login ulang terlebih dahulu.");
      return;
    }

    const coins = Number(account.coins ?? account.balance ?? 0);

    if (coins < cost) {
      showResult("⚠️ coins anda tidak cukup");
      return;
    }

    if (button) {
      button.disabled = true;
      button.textContent = "MEMPROSES...";
    }
    showResult("SEDANG MENGIRIM LIKE...");

    try {
      const result = await api("/api/like", {uid, region, service});
      const given = result.likes_given ?? result.LikesGivenByAPI ?? result.likesGiven ?? 0;
      const before = result.likes_before ?? result.LikesbeforeCommand ?? "-";
      const after = result.likes_after ?? result.LikesafterCommand ?? "-";
      const nickname = result.nickname || result.player_nickname || result.PlayerNickname || "-";

      showResult(
        `👤 Nickname : ${nickname}
🆔 UID : ${uid}
🌍 Region : ${result.region || (service === 'free' ? 'ID' : region)}

❤️ Like sebelum : ${before}
💗 Like sesudah : ${after}
🎁 Like diberikan : ${given}

📢 LIKE BERTAMBAH COINS DI KURANGI -${cost} ✅`
      );
      try {
        await refreshAccount();
      } catch (_) {}
    } catch (e) {
      const d = e.data || {};
      const errorText = String(d.message || d.error || e.message || "").toLowerCase();

      if (
        errorText.includes("coin tidak cukup") ||
        errorText.includes("coins tidak cukup") ||
        errorText.includes("insufficient coins") ||
        errorText.includes("saldo tidak cukup")
      ) {
        showResult(`📢 Coin tidak cukup. Isi ulang ${cost} coin untuk melanjutkan ✅`);
      } else {
        const given = Number(d.likes_given ?? 0);
        showResult(
          `👤 Nickname : ${d.nickname || "-"}
🆔 UID : ${d.uid || uid}
🌍 Region : ${d.region || (service === 'free' ? 'ID' : region)}

❤️ Like sebelum : ${d.likes_before ?? "-"}
💗 Like sesudah : ${d.likes_after ?? "-"}
🎁 Like diberikan : ${given}

${given === 0 && d.coins_refunded
  ? "📢 LIKE DIBERIKAN 0 — COINS DIKEMBALIKAN ✅"
  : "📢 LIKE GAGAL DIBERIKAN ❌"}`
        );
      }
      try {
        await refreshAccount();
      } catch (_) {}
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = oldText || "KIRIM LIKE";
      }
    }
  }, true);


  const redeemButton = document.createElement("button");
  redeemButton.id = "gx-redeem-button";
  redeemButton.type = "button";
  redeemButton.textContent = "🎁 KODE REDEEM";
  redeemButton.style.cssText = "display:block;width:fit-content;min-width:190px;max-width:none;margin:12px auto 20px;padding:12px 28px;border:1px solid #806cff;border-radius:12px;background:linear-gradient(90deg,#3158b8,#8b45c5);color:white;font-weight:900;font-size:14px;cursor:pointer;";
  const buyArea = document.querySelector(".gx-admin");
  if (buyArea) buyArea.insertAdjacentElement("afterend", redeemButton);

  redeemButton.addEventListener("click", async () => {
    if (!token) {
      showModal("login");
      message("Login terlebih dahulu untuk menggunakan kode redeem.");
      return;
    }
    const code = prompt("Masukan kode redeem");
    if (code === null) return;
    redeemButton.disabled = true;
    try {
      const result = await api("/api/redeem", {code: code.trim().toUpperCase()});
      alert(result.message || "Redeem berhasil!");
      await refreshAccount();
    } catch (e) {
      const d = e.data || {};
      alert(d.message || d.error || e.message || "Kode redeem gagal.");
    } finally {
      redeemButton.disabled = false;
    }
  });

  document.addEventListener("click", event => {
    const buy = event.target.closest("#gx-buy-coins, .gx-buy-coins");
    if (buy) {
      event.preventDefault();
      location.href = "/api/buy-coins";
    }
  }, true);

  document.addEventListener("click", event => {
    const nav = event.target.closest(
      ".gx-nav-free, .gx-nav-vip, [data-gx-page='free'], [data-gx-page='vip']"
    );
    if (nav && !token) {
      showModal("login");
      message("Buat akun terlebih dahulu untuk melanjutkan.");
    }
  }, true);

  window.addEventListener("pageshow", () => {
    refreshAccount();
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refreshAccount();
  });


  // GANZ X - OFC: Original TikTok Button Sound
  const gxButtonClickAudio = new Audio("/static/music/button-click.mp3?v=3");
  gxButtonClickAudio.preload = "auto";
  gxButtonClickAudio.volume = 0.85;

  document.addEventListener("click", event => {
    const el = event.target instanceof Element
      ? event.target.closest('button, input[type="button"], input[type="submit"], [role="button"]')
      : null;

    if (!el || el.disabled || el.dataset.noSound === "true") return;

    try {
      gxButtonClickAudio.currentTime = 0;
      const playback = gxButtonClickAudio.play();
      if (playback && typeof playback.catch === "function") {
        playback.catch(() => {});
      }
    } catch (_) {}
  }, true);

  refreshAccount();
})();
