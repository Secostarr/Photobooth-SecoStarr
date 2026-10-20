document.addEventListener("DOMContentLoaded", () => {
  const btnNewSession = document.getElementById("btnNewSession");
  const currentSession = document.getElementById("currentSession");

  if (btnNewSession) {
    btnNewSession.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/session/new", { method: "POST" });
        const data = await res.json();
        if (data.ok && currentSession) {
          currentSession.textContent = data.session_id;
        }
      } catch (err) {
        alert("Gagal membuat session baru: " + err.message);
      }
    });
  }

  const btnStartCapture = document.getElementById("btnStartCapture");
  const countdownBox = document.getElementById("countdownBox");
  const statusMsg = document.getElementById("statusMsg");

  if (btnStartCapture) {
    btnStartCapture.addEventListener("click", () => {
      let count = 3;
      if (countdownBox) countdownBox.textContent = String(count);
      if (statusMsg) statusMsg.textContent = "Bersiap untuk capture...";

      const timer = setInterval(() => {
        count -= 1;
        if (count > 0) {
          if (countdownBox) countdownBox.textContent = String(count);
        } else {
          clearInterval(timer);
          if (countdownBox) countdownBox.textContent = "FLASH!";
          if (statusMsg) statusMsg.textContent = "Foto terambil (simulasi web stage 1)";
          setTimeout(() => {
            if (countdownBox) countdownBox.textContent = "";
          }, 600);
        }
      }, 1000);
    });
  }
});
