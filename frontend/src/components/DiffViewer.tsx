import type { Snapshot } from "../api/client";
import api from "../api/client";
import ImageSlider from "./ImageSlider";

interface Props {
  currentSnapshot: Snapshot;
  previousSnapshot: Snapshot | null;
  mode: "side-by-side" | "overlay" | "diff";
}

export default function DiffViewer({
  currentSnapshot,
  previousSnapshot,
  mode,
}: Props) {
  const currentUrl = currentSnapshot.id
    ? api.getScreenshotUrl(currentSnapshot.id)
    : null;
  const previousUrl = previousSnapshot?.id
    ? api.getScreenshotUrl(previousSnapshot.id)
    : null;
  const diffUrl = currentSnapshot.diff_image_path
    ? api.getDiffImageUrl(currentSnapshot.id)
    : null;

  if (!currentUrl) {
    return (
      <div className="bg-surface border border-border rounded-xl p-8 text-center text-text-muted">
        Нет скриншота
      </div>
    );
  }

  if (mode === "diff" && diffUrl) {
    return (
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <img
          src={diffUrl}
          alt="Diff"
          className="w-full"
        />
      </div>
    );
  }

  if (mode === "overlay" && previousUrl && currentUrl) {
    return (
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <ImageSlider beforeUrl={previousUrl} afterUrl={currentUrl} />
      </div>
    );
  }

  // Side-by-side (default)
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {previousUrl && (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="text-xs text-text-muted px-3 py-2 border-b border-border">
            Предыдущий
          </div>
          <img
            src={previousUrl}
            alt="Previous"
            className="w-full"
          />
        </div>
      )}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="text-xs text-text-muted px-3 py-2 border-b border-border">
          Текущий
        </div>
        <img
          src={currentUrl}
          alt="Current"
          className="w-full"
        />
      </div>
    </div>
  );
}
