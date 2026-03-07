import { useEffect, useState } from "react";
import api, { type Page } from "../api/client";
import PageCard from "../components/PageCard";
import StatusBar from "../components/StatusBar";

type SortKey = "name" | "created_at" | "updated_at";

export default function PagesList() {
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>("created_at");

  useEffect(() => {
    loadPages();
  }, []);

  async function loadPages() {
    try {
      const data = await api.getPages();
      setPages(data);
    } catch (err) {
      console.error("Failed to load pages:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.deletePage(id);
      setPages((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  }

  async function handleToggle(id: string, active: boolean) {
    try {
      await api.updatePage(id, { is_active: active });
      setPages((prev) =>
        prev.map((p) => (p.id === id ? { ...p, is_active: active } : p))
      );
    } catch (err) {
      console.error("Failed to toggle:", err);
    }
  }

  const sorted = [...pages].sort((a, b) => {
    if (sortBy === "name") {
      return (a.name || a.url).localeCompare(b.name || b.url);
    }
    return new Date(b[sortBy]).getTime() - new Date(a[sortBy]).getTime();
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-text-muted">
        Загрузка...
      </div>
    );
  }

  return (
    <div>
      <StatusBar />

      {/* Sort controls */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold">Отслеживаемые страницы</h2>
        <div className="flex gap-2">
          {(
            [
              ["created_at", "По дате"],
              ["updated_at", "По проверке"],
              ["name", "По имени"],
            ] as [SortKey, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortBy(key)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                sortBy === key
                  ? "bg-accent/20 text-accent-light border-accent/30"
                  : "bg-surface text-text-dim border-border hover:border-accent/30"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {pages.length === 0 ? (
        <div className="text-center text-text-muted py-16">
          <p className="text-lg mb-2">Нет отслеживаемых страниц</p>
          <p className="text-sm">
            Добавьте первую страницу через форму или импорт
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sorted.map((page) => (
            <PageCard
              key={page.id}
              page={page}
              onDelete={handleDelete}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
