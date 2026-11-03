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
      <input id="gx-password" type="password" placeholder="Password" autocomplete="current-password">
      <button id="gx-auth-submit"></button>
      <button id="gx-auth-switch" class="gx-secondary">BELUM PUNYA AKUN? DAFTAR</button>

      <div id="gx-account-msg"></div>
    </div>`;
  document.body.appendChild(modal);

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
    if (headerName) headerName.textContent = displayName;
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
    if (headerName) headerName.textContent = displayName;
    if (usernameBox) usernameBox.textContent = account.username || "AKUN";
    if (coinsBox) coinsBox.textContent = "🪙 " + (account.coins ?? 0);
    setProfileAvatar(account.avatar_url || "/static/profil.webp");
  }

  function escapeHtml(value) {
    const el = document.createElement("span");
    el.textContent = String(value ?? "");
    return el.innerHTML;
  }

  async function loadTopCoins() {
    const list = document.getElementById("gx-topcoins-list");
    if (!list) return;
    list.textContent = "Memuat leaderboard...";
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
          <img src="${escapeHtml(user.avatar_url)}" alt="" loading="lazy" decoding="async" fetchpriority="low" onerror="this.src='/static/profil.webp'">
          <div class="gx-topcoin-name">${escapeHtml(user.username)}</div>
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
    if (file.size > 1024 * 1024) {
      $("#gx-profile-message").textContent = "Ukuran foto maksimal 1 MB.";
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
      $("#gx-profile-message").textContent = "Foto profil berhasil diperbarui.";
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
      $("#gx-profile-message").textContent = result.message || "Nama berhasil disimpan.";
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
      const before = result.likes_before ?? result.LikesbeforeCommand ?? "Belum diketahui";
      const after = result.likes_after ?? result.LikesafterCommand ?? "Belum diketahui";
      const nickname = result.nickname || result.player_nickname || result.PlayerNickname || "Tidak diketahui";

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
${given > 0 ? "" : "\n📢 LIKE DIBERIKAN 0 — COINS DIKEMBALIKAN ✅"}`
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
    const code = prompt("Masukkan kode redeem 8 huruf:");
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

  refreshAccount();
})();
