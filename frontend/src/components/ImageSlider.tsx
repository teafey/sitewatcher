import { useRef, useState, useCallback } from "react";

interface Props {
  beforeUrl: string;
  afterUrl: string;
  overlayUrl?: string;
}

export default function ImageSlider({ beforeUrl, afterUrl, overlayUrl }: Props) {
  const [position, setPosition] = useState(50);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);

  const handleMove = useCallback(
    (clientX: number) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const percent = Math.max(0, Math.min(100, (x / rect.width) * 100));
      setPosition(percent);
    },
    []
  );

  const handleMouseDown = () => {
    isDragging.current = true;
  };

  const handleMouseUp = () => {
    isDragging.current = false;
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging.current) handleMove(e.clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    handleMove(e.touches[0].clientX);
  };

  return (
    <div
      ref={containerRef}
      className="relative select-none cursor-col-resize overflow-hidden"
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onMouseMove={handleMouseMove}
      onTouchMove={handleTouchMove}
    >
      {/* After (full width) */}
      <div className="relative">
        <img src={afterUrl} alt="After" className="w-full block" />
        {overlayUrl && (
          <img
            src={overlayUrl}
            alt="Diff overlay"
            className="absolute top-0 left-0 w-full h-full opacity-40 mix-blend-multiply"
          />
        )}
      </div>

      {/* Before (clipped) */}
      <div
        className="absolute top-0 left-0 w-full h-full overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
      >
        <img
          src={beforeUrl}
          alt="Before"
          className="w-full block"
        />
      </div>

      {/* Slider line */}
      <div
        className="absolute top-0 h-full w-0.5 bg-white shadow-lg"
        style={{ left: `${position}%` }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full shadow flex items-center justify-center">
          <span className="text-gray-800 text-xs font-bold">⟷</span>
        </div>
      </div>

      {/* Labels */}
      <div className="absolute top-2 left-2 text-xs bg-black/60 text-white px-2 py-1 rounded">
        До
      </div>
      <div className="absolute top-2 right-2 text-xs bg-black/60 text-white px-2 py-1 rounded">
        После
      </div>
    </div>
  );
}
