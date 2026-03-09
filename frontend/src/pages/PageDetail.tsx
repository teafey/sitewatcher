import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api, { type Page, type Snapshot } from "../api/client";
import SnapshotTimeline from "../components/SnapshotTimeline";
import DiffViewer from "../components/DiffViewer";
import TextDiff from "../components/TextDiff";

export default function PageDetail() {
  const { pageId } = useParams<{ pageId: string }>();
  const [page, setPage] = useState<Page | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(
    null
  );
  const [prevSnapshot, setPrevSnapshot] = useState<Snapshot | null>(null);
  const [textDiff, setTextDiff] = useState<string>("");
  const [viewMode, setViewMode] = useState<"side-by-side" | "overlay" | "diff">(
    "side-by-side"
  );
  const [checking, setChecking] = useState(false);

  const handleDeleteSnapshot = async (snap: Snapshot) => {
    try {
      await api.deleteSnapshot(snap.id);
      setSnapshots((prev) => {
        const next = prev.filter((s) => s.id !== snap.id);
        if (selectedSnapshot?.id === snap.id) {
          const idx = prev.findIndex((s) => s.id === snap.id);
          const replacement = next[idx] || next[idx - 1] || null;
          setSelectedSnapshot(replacement);
          const prevIdx = replacement ? next.indexOf(replacement) + 1 : -1;
          setPrevSnapshot(prevIdx >= 0 && prevIdx < next.length ? next[prevIdx] : null);
        }
        return next;
      });
    } catch (err) {
      console.error("Failed to delete snapshot", err);
    }
  };

  const loadSnapshots = (selectFirst = true) => {
    if (!pageId) return;
    api
      .getSnapshots(pageId, { limit: 50 })
      .then((snaps) => {
        setSnapshots(snaps);
        if (selectFirst && snaps.length > 0) {
          setSelectedSnapshot(snaps[0]);
          if (snaps.length > 1) setPrevSnapshot(snaps[1]);
        }
      })
      .catch(console.error);
  };

  const handleCheck = async () => {
    if (!page || checking) return;
    setChecking(true);
    try {
      await api.triggerCheckPage(page.id);
      // Poll for new snapshot
      const prevCount = snapshots.length;
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const snaps = await api.getSnapshots(page.id, { limit: 50 });
          if (snaps.length > prevCount || attempts >= 20) {
            clearInterval(poll);
            setSnapshots(snaps);
            if (snaps.length > 0) {
              setSelectedSnapshot(snaps[0]);
              if (snaps.length > 1) setPrevSnapshot(snaps[1]);
            }
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

  useEffect(() => {
    if (!pageId) return;
    api.getPage(pageId).then(setPage).catch(console.error);
    loadSnapshots();
  }, [pageId]);

  useEffect(() => {
    if (selectedSnapshot?.id) {
      api.getTextDiff(selectedSnapshot.id).then(setTextDiff).catch(console.error);
    }
  }, [selectedSnapshot?.id]);

  if (!page) {
    return (
      <div className="text-text-muted text-center py-16">Загрузка...</div>
    );
  }

  return (
    <div>
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-sm text-text-muted mb-6">
        <Link to="/" className="hover:text-white transition-colors">
          Все страницы
        </Link>
        <span>/</span>
        <span className="text-white">{page.name || page.url}</span>
        {selectedSnapshot && (
          <>
            <span>/</span>
            <span>
              {new Date(selectedSnapshot.captured_at).toLocaleString("ru")}
            </span>
          </>
        )}
      </div>

      {/* Page info */}
      <div className="bg-surface border border-border rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold">{page.name || page.url}</h1>
            <p className="text-sm text-text-muted mt-1">{page.url}</p>
            <div className="flex gap-4 mt-2 text-xs text-text-dim">
              <span>
                Viewport: {page.viewport_width}x{page.viewport_height}
              </span>
              <span>Порог: {page.diff_threshold}%</span>
              <span>Интервал: {page.check_interval_hours}ч</span>
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              to={`/edit/${page.id}`}
              className="text-xs px-4 py-2 bg-surface-2 text-text-dim border border-border rounded-lg hover:border-accent/30 transition"
            >
              Настройки
            </Link>
            <button
              onClick={handleCheck}
              disabled={checking}
              className="text-xs px-4 py-2 bg-accent/10 text-accent-light border border-accent/20 rounded-lg hover:bg-accent/20 transition disabled:opacity-50"
            >
              {checking ? "Проверяю..." : "Проверить сейчас"}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-1">
          <SnapshotTimeline
            snapshots={snapshots}
            selectedId={selectedSnapshot?.id || null}
            onSelect={(snap) => {
              const idx = snapshots.findIndex((s) => s.id === snap.id);
              setSelectedSnapshot(snap);
              setPrevSnapshot(snapshots[idx + 1] || null);
            }}
            onDelete={handleDeleteSnapshot}
          />
        </div>

        {/* Diff viewer */}
        <div className="lg:col-span-3">
          {/* View mode toggle */}
          <div className="flex gap-2 mb-4">
            {(
              [
                ["side-by-side", "Рядом"],
                ["overlay", "Наложение"],
                ["diff", "Diff"],
              ] as [typeof viewMode, string][]
            ).map(([mode, label]) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                  viewMode === mode
                    ? "bg-accent/20 text-accent-light border-accent/30"
                    : "bg-surface text-text-dim border-border hover:border-accent/30"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {selectedSnapshot ? (
            <DiffViewer
              currentSnapshot={selectedSnapshot}
              previousSnapshot={prevSnapshot}
              mode={viewMode}
            />
          ) : (
            <div className="text-text-muted text-center py-16">
              Нет снимков для отображения
            </div>
          )}

          {/* Text diff */}
          {textDiff && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold mb-3">Текстовые изменения</h3>
              <TextDiff diff={textDiff} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
