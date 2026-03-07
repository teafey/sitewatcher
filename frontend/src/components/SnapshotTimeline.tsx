import type { Snapshot } from "../api/client";

interface Props {
  snapshots: Snapshot[];
  selectedId: string | null;
  onSelect: (snapshot: Snapshot) => void;
}

export default function SnapshotTimeline({
  snapshots,
  selectedId,
  onSelect,
}: Props) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4">
      <h3 className="text-sm font-semibold mb-4">История снимков</h3>
      <div className="space-y-1">
        {snapshots.map((snap) => {
          const isSelected = snap.id === selectedId;
          const hasChanges = snap.has_changes;
          const hasError = !!snap.error_message;

          return (
            <button
              key={snap.id}
              onClick={() => onSelect(snap)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition ${
                isSelected
                  ? "bg-accent/10 border border-accent/30"
                  : "hover:bg-surface-2 border border-transparent"
              }`}
            >
              {/* Dot */}
              <span
                className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                  hasError
                    ? "bg-red-500"
                    : hasChanges
                      ? "bg-red-500"
                      : "bg-green-500"
                }`}
              />

              {/* Info */}
              <div className="min-w-0">
                <p className="text-xs text-text-dim truncate">
                  {new Date(snap.captured_at).toLocaleString("ru")}
                </p>
                {hasChanges && snap.diff_percent != null && (
                  <p className="text-[10px] text-red-400">
                    {snap.diff_percent.toFixed(2)}% изменений
                  </p>
                )}
                {hasError && (
                  <p className="text-[10px] text-red-400 truncate">
                    {snap.error_message}
                  </p>
                )}
              </div>
            </button>
          );
        })}

        {snapshots.length === 0 && (
          <p className="text-xs text-text-muted text-center py-4">
            Нет снимков
          </p>
        )}
      </div>
    </div>
  );
}
