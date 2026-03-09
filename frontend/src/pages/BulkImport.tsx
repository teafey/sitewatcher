import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import ViewportPresets from "../components/ViewportPresets";

export default function BulkImport() {
  const navigate = useNavigate();
  const [urls, setUrls] = useState("");
  const [viewports, setViewports] = useState<{ width: number; height: number }[]>([
    { width: 1920, height: 1080 },
  ]);
  const [importing, setImporting] = useState(false);
  const [results, setResults] = useState<
    { url: string; success: boolean; error?: string }[]
  >([]);

  function handleToggleViewport(w: number, h: number) {
    setViewports((prev) => {
      const exists = prev.some((v) => v.width === w && v.height === h);
      if (exists) {
        return prev.filter((v) => !(v.width === w && v.height === h));
      }
      return [...prev, { width: w, height: h }];
    });
  }

  async function handleImport() {
    const urlList = urls
      .split("\n")
      .map((u) => u.trim())
      .filter(Boolean);

    if (urlList.length === 0) {
      alert("Введите хотя бы один URL");
      return;
    }

    setImporting(true);
    const importResults: typeof results = [];

    for (const url of urlList) {
      try {
        await api.createPage({
          url,
          name: new URL(url).hostname,
          viewports,
          viewport_width: viewports[0].width,
          viewport_height: viewports[0].height,
          diff_threshold: 0.5,
        } as Parameters<typeof api.createPage>[0]);
        importResults.push({ url, success: true });
      } catch (err) {
        importResults.push({
          url,
          success: false,
          error: err instanceof Error ? err.message : "Unknown error",
        });
      }
    }

    setResults(importResults);
    setImporting(false);
  }

  const successCount = results.filter((r) => r.success).length;
  const errorCount = results.filter((r) => !r.success).length;

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold mb-6">Массовый импорт</h1>

      <div className="bg-surface border border-border rounded-xl p-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-text-dim mb-2">
            Viewport
          </label>
          <ViewportPresets
            mode="multi"
            selected={viewports}
            onToggle={handleToggleViewport}
          />
        </div>

        <label className="block text-sm font-medium text-text-dim mb-2">
          URL-адреса (один на строку)
        </label>
        <textarea
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          rows={10}
          placeholder={
            "https://example.com\nhttps://example.org\nhttps://httpbin.org/html"
          }
          className="w-full bg-surface-2 border border-border rounded-lg px-4 py-3 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent font-mono"
        />

        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-text-muted">
            {urls.split("\n").filter((u) => u.trim()).length} URL
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => navigate("/")}
              className="px-4 py-2 text-sm bg-surface-2 text-text-dim border border-border rounded-lg hover:border-accent/30 transition"
            >
              Отмена
            </button>
            <button
              onClick={handleImport}
              disabled={importing}
              className="px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/80 transition disabled:opacity-50"
            >
              {importing ? "Импорт..." : "Импортировать"}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="mt-6 bg-surface border border-border rounded-xl p-6">
          <h3 className="text-sm font-semibold mb-3">
            Результат: {successCount} добавлено, {errorCount} ошибок
          </h3>
          <div className="space-y-2">
            {results.map((r, i) => (
              <div
                key={i}
                className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${
                  r.success
                    ? "bg-green-500/10 text-green-400"
                    : "bg-red-500/10 text-red-400"
                }`}
              >
                <span>{r.success ? "✓" : "✕"}</span>
                <span className="truncate">{r.url}</span>
                {r.error && (
                  <span className="ml-auto text-text-muted">{r.error}</span>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={() => navigate("/")}
            className="mt-4 px-4 py-2 text-sm bg-accent text-white rounded-lg hover:bg-accent/80 transition"
          >
            К списку страниц
          </button>
        </div>
      )}
    </div>
  );
}
