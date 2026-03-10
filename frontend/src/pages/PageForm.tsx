import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { type Project } from "../api/client";
import ViewportPresets from "../components/ViewportPresets";

export default function PageForm() {
  const navigate = useNavigate();
  const { pageId, projectId } = useParams<{ pageId: string; projectId: string }>();
  const isEdit = !!pageId;
  const [project, setProject] = useState<Project | null>(null);

  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [viewports, setViewports] = useState<{ width: number; height: number }[]>([
    { width: 1920, height: 1080 },
  ]);
  const [diffThreshold, setDiffThreshold] = useState(0.5);
  const [ignoreSelectors, setIgnoreSelectors] = useState("");
  const [waitForSelector, setWaitForSelector] = useState("");
  const [checkInterval, setCheckInterval] = useState(24);
  const [saving, setSaving] = useState(false);
  const [scrollToBottom, setScrollToBottom] = useState(true);
  const [maxScrolls, setMaxScrolls] = useState(10);
  const [waitSeconds, setWaitSeconds] = useState(3);

  useEffect(() => {
    if (pageId) {
      api.getPage(pageId).then((page) => {
        setUrl(page.url);
        setName(page.name || "");
        if (page.project_id) {
          api.getProject(page.project_id).then(setProject).catch(console.error);
        }
        // Init viewports from page.viewports or fallback to single viewport
        if (page.viewports && page.viewports.length > 0) {
          setViewports(page.viewports);
        } else {
          setViewports([{ width: page.viewport_width, height: page.viewport_height }]);
        }
        setDiffThreshold(page.diff_threshold);
        setIgnoreSelectors((page.ignore_selectors || []).join("\n"));
        setWaitForSelector(page.wait_for_selector || "");
        setCheckInterval(page.check_interval_hours);
        setScrollToBottom(page.scroll_to_bottom ?? true);
        setMaxScrolls(page.max_scrolls ?? 10);
        setWaitSeconds(page.wait_seconds ?? 3);
      });
    } else if (projectId) {
      api.getProject(projectId).then(setProject).catch(console.error);
    }
  }, [pageId, projectId]);

  function handleToggleViewport(w: number, h: number) {
    setViewports((prev) => {
      const exists = prev.some((v) => v.width === w && v.height === h);
      if (exists) {
        return prev.filter((v) => !(v.width === w && v.height === h));
      }
      return [...prev, { width: w, height: h }];
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const data: Record<string, unknown> = {
      url,
      name: name || null,
      project_id: isEdit ? projectId || null : project?.id || projectId || null,
      viewports,
      // Keep compat fields from first viewport
      viewport_width: viewports[0].width,
      viewport_height: viewports[0].height,
      diff_threshold: diffThreshold,
      ignore_selectors: ignoreSelectors
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
      wait_for_selector: waitForSelector || null,
      check_interval_hours: checkInterval,
      scroll_to_bottom: scrollToBottom,
      max_scrolls: maxScrolls,
      wait_seconds: waitSeconds,
    };

    try {
      const savedPage = isEdit && pageId
        ? await api.updatePage(pageId, data)
        : await api.createPage(data);
      navigate(savedPage.project_id ? `/projects/${savedPage.project_id}` : "/");
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
      {project && (
        <div className="mb-6 bg-surface border border-border rounded-xl p-4">
          <div className="text-xs uppercase tracking-wider text-text-muted mb-1">
            Проект
          </div>
          <div className="text-sm text-white font-medium">{project.name}</div>
          <div className="text-xs text-text-muted mt-1">{project.base_url}</div>
        </div>
      )}

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
          {!project && !projectId && (
            <p className="text-xs text-text-muted mt-1">
              Проект будет определён автоматически по домену URL
            </p>
          )}
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
            mode="multi"
            selected={viewports}
            onToggle={handleToggleViewport}
          />
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

        {/* Capture settings */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-text-dim">Настройки загрузки</h3>

          {/* Scroll toggle */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={scrollToBottom}
              onChange={(e) => setScrollToBottom(e.target.checked)}
              className="w-4 h-4 accent-accent"
            />
            <span className="text-sm text-white">
              Прокручивать страницу (для lazy-load контента)
            </span>
          </label>

          {scrollToBottom && (
            <div>
              <label className="block text-xs text-text-muted mb-1">
                Максимум прокруток (экранов)
              </label>
              <input
                type="number"
                value={maxScrolls}
                onChange={(e) => setMaxScrolls(Number(e.target.value))}
                min={1}
                max={100}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
          )}

          {/* Wait seconds */}
          <div>
            <label className="block text-xs text-text-muted mb-1">
              Ожидание после загрузки (сек)
            </label>
            <input
              type="number"
              value={waitSeconds}
              onChange={(e) => setWaitSeconds(Number(e.target.value))}
              min={1}
              max={30}
              className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>
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
            onClick={() =>
              navigate(project?.id || projectId ? `/projects/${project?.id || projectId}` : "/")
            }
            className="px-6 py-2.5 bg-surface-2 text-text-dim border border-border rounded-lg hover:border-accent/30 transition"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
