export const VIEWPORT_PRESETS = [
  { label: "Desktop", width: 1920, height: 1080 },
  { label: "Планшет", width: 768, height: 1024 },
  { label: "Мобильный", width: 375, height: 812 },
] as const;

export function getViewportLabel(w: number, h: number): string {
  if (w === 1920 && h === 1080) return "Desktop";
  if (w === 768 && h === 1024) return "Планшет";
  if (w === 375 && h === 812) return "Мобильный";
  return `${w}×${h}`;
}

// --- Single-select mode (legacy) ---
interface SingleProps {
  mode?: "single";
  onSelect: (width: number, height: number) => void;
  activeWidth: number;
  activeHeight: number;
}

// --- Multi-select mode ---
interface MultiProps {
  mode: "multi";
  selected: { width: number; height: number }[];
  onToggle: (width: number, height: number) => void;
}

type Props = SingleProps | MultiProps;

export default function ViewportPresets(props: Props) {
  if (props.mode === "multi") {
    const { selected, onToggle } = props;
    return (
      <div className="flex gap-2">
        {VIEWPORT_PRESETS.map((preset) => {
          const isActive = selected.some(
            (v) => v.width === preset.width && v.height === preset.height
          );
          return (
            <button
              key={preset.label}
              type="button"
              onClick={() => {
                // Prevent deselecting the last one
                if (isActive && selected.length <= 1) return;
                onToggle(preset.width, preset.height);
              }}
              className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                isActive
                  ? "bg-accent/20 text-accent-light border-accent/30"
                  : "bg-surface-2 text-text-dim border-border hover:border-accent/30"
              }`}
            >
              {preset.label}
              <span className="ml-1 text-text-muted">
                {preset.width}×{preset.height}
              </span>
            </button>
          );
        })}
      </div>
    );
  }

  // Single-select mode
  const { onSelect, activeWidth, activeHeight } = props;
  return (
    <div className="flex gap-2">
      {VIEWPORT_PRESETS.map((preset) => {
        const isActive =
          activeWidth === preset.width && activeHeight === preset.height;
        return (
          <button
            key={preset.label}
            type="button"
            onClick={() => onSelect(preset.width, preset.height)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition ${
              isActive
                ? "bg-accent/20 text-accent-light border-accent/30"
                : "bg-surface-2 text-text-dim border-border hover:border-accent/30"
            }`}
          >
            {preset.label}
            <span className="ml-1 text-text-muted">
              {preset.width}×{preset.height}
            </span>
          </button>
        );
      })}
    </div>
  );
}
