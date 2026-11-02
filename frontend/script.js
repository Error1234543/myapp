// Set this to the deployed Koyeb API URL, for example:
// window.TOOLNEX_API_BASE = "https://your-service.koyeb.app";
const API_BASE = (window.TOOLNEX_API_BASE || "").replace(/\/$/, "");
const toast = document.getElementById("toast");
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
}

document.getElementById("year").textContent = new Date().getFullYear();

const search = document.getElementById("toolSearch");
const cards = [...document.querySelectorAll(".tool-card")];
const filters = [...document.querySelectorAll(".filter")];
let activeFilter = "all";

function filterTools() {
  const query = search.value.trim().toLowerCase();
  let visible = 0;
  cards.forEach(card => {
    const matchesQuery = (card.dataset.search + " " + card.textContent).toLowerCase().includes(query);
    const matchesCategory = activeFilter === "all" || card.dataset.category === activeFilter;
    const show = matchesQuery && matchesCategory;
    card.hidden = !show;
    if (show) visible++;
  });
  document.getElementById("toolCount").textContent = visible + (visible === 1 ? " tool" : " tools");
  document.getElementById("noResults").hidden = visible !== 0;
}
search.addEventListener("input", filterTools);
filters.forEach(button => button.addEventListener("click", () => {
  filters.forEach(item => item.classList.toggle("active", item === button));
  activeFilter = button.dataset.filter;
  filterTools();
}));
document.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    search.focus();
  }
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

document.querySelectorAll(".tool-panel form").forEach(form => {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = form.querySelector(".action-btn");
    const original = button.innerHTML;
    const resultBox = form.querySelector(".inline-result");
    button.disabled = true;
    button.textContent = "Processing…";
    if (resultBox) resultBox.textContent = "";

    try {
      if (!API_BASE) throw new Error("Backend URL abhi connect nahi hua. Koyeb deploy ke baad API URL script.js mein set karenge.");
      const endpoint = API_BASE + form.dataset.endpoint;
      let response;
      if (form.dataset.json === "true") {
        const text = form.elements.text.value;
        response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
        });
        if (!response.ok) throw new Error((await response.json()).detail || "Request failed.");
        const data = await response.json();
        resultBox.textContent = `Words: ${data.words} · Characters: ${data.characters} · Without spaces: ${data.characters_without_spaces} · Lines: ${data.lines}`;
        return;
      }

      const body = new FormData(form);
      response = await fetch(endpoint, { method: "POST", body });
      if (!response.ok) {
        let message = "Processing failed.";
        try { const error = await response.json(); message = error.detail || message; } catch {}
        throw new Error(message);
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      downloadBlob(blob, match ? match[1] : "toolnex-result");
      showToast("Done! Your download is ready.");
    } catch (error) {
      showToast(error.message || "Something went wrong.");
    } finally {
      button.disabled = false;
      button.innerHTML = original;
    }
  });
});
