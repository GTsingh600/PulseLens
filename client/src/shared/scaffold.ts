import { getHealth } from "./api";

/** Placeholder page body used until the real page lands (M1.3, M2.1, M3.4). */
export function renderScaffold(title: string, note: string): void {
  const app = document.getElementById("app");
  if (!app) return;
  const h1 = document.createElement("h1");
  h1.textContent = title;
  const p = document.createElement("p");
  p.textContent = note;
  const status = document.createElement("p");
  status.className = "muted";
  status.dataset.testid = "server-status";
  status.textContent = "Server: checking...";
  app.append(h1, p, status);
  void getHealth().then((h) => {
    status.textContent = h ? `Server: ok (v${h.version})` : "Server: offline";
  });
}
