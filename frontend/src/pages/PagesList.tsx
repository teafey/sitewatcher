import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { type Page, type Project } from "../api/client";
import PageCard from "../components/PageCard";

type SortKey = "name" | "created_at" | "updated_at";

export default function PagesList() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>("created_at");

  useEffect(() => {
    if (!projectId) return;
    loadProject(projectId);
    loadPages(projectId);
  }, [projectId]);

  async function loadProject(id: string) {
    try {
      const data = await api.getProject(id);
      setProject(data);
    } catch (err) {
      console.error("Failed to load project:", err);
    }
  }

  async function loadPages(id: string) {
    try {
      const data = await api.getProjectPages(id);
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 text-sm text-text-muted mb-2">
            <Link to="/" className="hover:text-white transition-colors">
              Проекты
            </Link>
            <span>/</span>
            <span className="text-white">{project?.name || "Проект"}</span>
          </div>
          <h2 className="text-lg font-bold">{project?.name || "Страницы проекта"}</h2>
          {project && (
            <p className="text-sm text-text-muted mt-1">{project.base_url}</p>
          )}
        </div>
        <div className="flex gap-2 items-center">
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
          {projectId && (
            <Link
              to={`/projects/${projectId}/add`}
              className="text-xs px-3 py-1.5 rounded-lg bg-accent text-white hover:bg-accent/80 transition"
            >
              Добавить страницу
            </Link>
          )}
        </div>
      </div>

      {pages.length === 0 ? (
        <div className="text-center text-text-muted py-16">
          <p className="text-lg mb-2">В проекте пока нет страниц</p>
          <p className="text-sm">Добавьте первую страницу для этого сайта</p>
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
