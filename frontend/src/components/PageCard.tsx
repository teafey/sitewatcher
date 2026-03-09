import { Link } from "react-router-dom";
import api, { type Page, type Snapshot } from "../api/client";
import { useEffect, useState } from "react";

interface Props {
  page: Page;
  onDelete: (id: string) => void;
  onToggle: (id: string, active: boolean) => void;
}

export default function PageCard({ page, onDelete, onToggle }: Props) {
  const [latestSnapshot, setLatestSnapshot] = useState<Snapshot | null>(null);
  const [checking, setChecking] = useState(false);

  const loadSnapshot = () => {
    api
      .getSnapshots(page.id, { limit: 1 })
      .then((snaps) => setLatestSnapshot(snaps[0] || null))
      .catch(console.error);
  };

  useEffect(() => {
    loadSnapshot();
  }, [page.id]);

  const handleCheck = async () => {
    if (checking) return;
    setChecking(true);
    try {
      await api.triggerCheckPage(page.id);
      const prevId = latestSnapshot?.id;
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const snaps = await api.getSnapshots(page.id, { limit: 1 });
          if ((snaps[0] && snaps[0].id !== prevId) || attempts >= 20) {
            clearInterval(poll);
            setLatestSnapshot(snaps[0] || null);
            setChecking(false);
          }
        } catch {
          clearInterval(poll);
          setChecking(false);
        }
      }, 3000);
    } catch {
      setChecking(false);
    }
  };

  const status = getStatus(page, latestSnapshot);

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden hover:border-accent/50 transition-colors">
      {/* Thumbnail */}
      <div className="h-40 bg-surface-2 relative overflow-hidden">
        {latestSnapshot?.id ? (
          <img
            src={api.getScreenshotUrl(latestSnapshot.id)}
            alt={page.name || page.url}
            className="w-full h-full object-cover object-top"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-text-muted text-sm">
            Нет снимка
          </div>
        )}
        <div className="absolute top-2 right-2">
          <span
            className={`inline-block w-3 h-3 rounded-full ${status.dotColor}`}
            title={status.label}
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <Link
          to={`/pages/${page.id}`}
          className="text-sm font-semibold text-white hover:text-accent-light transition-colors block truncate"
        >
          {page.name || page.url}
        </Link>
        <p className="text-xs text-text-muted truncate mt-1">{page.url}</p>

        <div className="flex items-center gap-2 mt-2 text-xs text-text-dim">
          <span>
            {page.viewport_width}×{page.viewport_height}
          </span>
          <span>·</span>
          <span>Порог: {page.diff_threshold}%</span>
        </div>

        {latestSnapshot?.captured_at && (
          <p className="text-xs text-text-muted mt-1">
            {new Date(latestSnapshot.captured_at).toLocaleString("ru")}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2 mt-3">
          <button
            onClick={handleCheck}
            disabled={checking}
            className="flex-1 text-xs px-3 py-1.5 bg-accent/10 text-accent-light border border-accent/20 rounded-lg hover:bg-accent/20 transition disabled:opacity-50"
          >
            {checking ? "Проверяю..." : "Проверить"}
          </button>
          <button
            onClick={() => onToggle(page.id, !page.is_active)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition ${
              page.is_active
                ? "bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20"
                : "bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20"
            }`}
          >
            {page.is_active ? "Откл" : "Вкл"}
          </button>
          <button
            onClick={() => {
              if (confirm("Удалить страницу?")) onDelete(page.id);
            }}
            className="text-xs px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg hover:bg-red-500/20 transition"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

function getStatus(page: Page, snapshot: Snapshot | null) {
  if (!page.is_active) return { dotColor: "bg-gray-500", label: "Неактивна" };
  if (!snapshot) return { dotColor: "bg-gray-400", label: "Новая" };
  if (snapshot.error_message) return { dotColor: "bg-red-500", label: "Ошибка" };
  if (snapshot.has_changes) return { dotColor: "bg-red-500", label: "Изменения" };
  return { dotColor: "bg-green-500", label: "OK" };
}
