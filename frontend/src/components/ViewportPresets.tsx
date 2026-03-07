interface Props {
  onSelect: (width: number, height: number) => void;
  activeWidth: number;
  activeHeight: number;
}

const PRESETS = [
  { label: "Desktop", width: 1920, height: 1080 },
  { label: "Tablet", width: 768, height: 1024 },
  { label: "Mobile", width: 375, height: 812 },
] as const;

export default function ViewportPresets({
  onSelect,
  activeWidth,
  activeHeight,
}: Props) {
  return (
    <div className="flex gap-2">
      {PRESETS.map((preset) => {
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
