import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api/client";
import ViewportPresets from "../components/ViewportPresets";

export default function PageForm() {
  const navigate = useNavigate();
  const { pageId } = useParams<{ pageId: string }>();
  const isEdit = !!pageId;

  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [viewportWidth, setViewportWidth] = useState(1920);
  const [viewportHeight, setViewportHeight] = useState(1080);
  const [diffThreshold, setDiffThreshold] = useState(0.5);
  const [ignoreSelectors, setIgnoreSelectors] = useState("");
  const [waitForSelector, setWaitForSelector] = useState("");
  const [checkInterval, setCheckInterval] = useState(24);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (pageId) {
      api.getPage(pageId).then((page) => {
        setUrl(page.url);
        setName(page.name || "");
        setViewportWidth(page.viewport_width);
        setViewportHeight(page.viewport_height);
        setDiffThreshold(page.diff_threshold);
        setIgnoreSelectors((page.ignore_selectors || []).join("\n"));
        setWaitForSelector(page.wait_for_selector || "");
        setCheckInterval(page.check_interval_hours);
      });
    }
  }, [pageId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const data = {
      url,
      name: name || null,
      viewport_width: viewportWidth,
      viewport_height: viewportHeight,
      diff_threshold: diffThreshold,
      ignore_selectors: ignoreSelectors
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      wait_for_selector: waitForSelector || null,
      check_interval_hours: checkInterval,
    };

    try {
      if (isEdit && pageId) {
        await api.updatePage(pageId, data);
      } else {
        await api.createPage(data);
      }
      navigate("/");
    } catch (err) {
      console.error("Save failed:", err);
      alert("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold mb-6">
        {isEdit ? "Редактирование страницы" : "Добавить страницу"}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* URL */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            URL *
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            placeholder="https://example.com"
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Название
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Мой сайт — главная"
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Viewport */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Viewport
          </label>
          <ViewportPresets
            onSelect={(w, h) => {
              setViewportWidth(w);
              setViewportHeight(h);
            }}
            activeWidth={viewportWidth}
            activeHeight={viewportHeight}
          />
          <div className="flex gap-3 mt-3">
            <div className="flex-1">
              <label className="block text-xs text-text-muted mb-1">
                Ширина
              </label>
              <input
                type="number"
                value={viewportWidth}
                onChange={(e) => setViewportWidth(Number(e.target.value))}
                min={320}
                max={3840}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-text-muted mb-1">
                Высота
              </label>
              <input
                type="number"
                value={viewportHeight}
                onChange={(e) => setViewportHeight(Number(e.target.value))}
                min={240}
                max={2160}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
          </div>
        </div>

        {/* Threshold */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Порог чувствительности: {diffThreshold}%
          </label>
          <input
            type="range"
            value={diffThreshold}
            onChange={(e) => setDiffThreshold(Number(e.target.value))}
            min={0.1}
            max={10}
            step={0.1}
            className="w-full accent-accent"
          />
          <div className="flex justify-between text-xs text-text-muted mt-1">
            <span>0.1% (чувствительный)</span>
            <span>10% (грубый)</span>
          </div>
        </div>

        {/* Check interval */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Интервал проверки (часы)
          </label>
          <input
            type="number"
            value={checkInterval}
            onChange={(e) => setCheckInterval(Number(e.target.value))}
            min={1}
            max={720}
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
          />
        </div>

        {/* Ignore selectors */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            CSS-селекторы для игнорирования
          </label>
          <textarea
            value={ignoreSelectors}
            onChange={(e) => setIgnoreSelectors(e.target.value)}
            rows={3}
            placeholder={".cookie-banner\n#dynamic-counter\n.ads"}
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent font-mono"
          />
          <p className="text-xs text-text-muted mt-1">
            Один селектор на строку. Эти элементы будут удалены перед скриншотом.
          </p>
        </div>

        {/* Wait for selector */}
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Ожидать элемент (для SPA)
          </label>
          <input
            type="text"
            value={waitForSelector}
            onChange={(e) => setWaitForSelector(e.target.value)}
            placeholder="#main-content"
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent font-mono"
          />
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-accent text-white rounded-lg hover:bg-accent/80 transition disabled:opacity-50"
          >
            {saving
              ? "Сохранение..."
              : isEdit
                ? "Сохранить"
                : "Добавить и сделать снимок"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="px-6 py-2.5 bg-surface-2 text-text-dim border border-border rounded-lg hover:border-accent/30 transition"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
