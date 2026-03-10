import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { type ProjectRow } from "../api/client";
import StatusBar from "../components/StatusBar";

type SortKey = "name" | "pages_count" | "attention_count";

export default function ProjectsList() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>("attention_count");

  useEffect(() => {
    api
      .getProjects()
      .then(setProjects)
      .catch((err) => console.error("Failed to load projects:", err))
      .finally(() => setLoading(false));
  }, []);

  const sorted = [...projects].sort((a, b) => {
    if (sortBy === "name") {
      return a.name.localeCompare(b.name, "ru");
    }
    return b[sortBy] - a[sortBy];
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

      <div className="flex items-center justify-between mb-6 gap-4">
        <div>
          <h2 className="text-lg font-bold">Проекты</h2>
          <p className="text-sm text-text-muted mt-1">
            Сайты сгруппированы по домену, страницы открываются внутри проекта
          </p>
        </div>
        <div className="flex gap-2">
          {(
            [
              ["attention_count", "По вниманию"],
              ["pages_count", "По страницам"],
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

      {projects.length === 0 ? (
        <div className="text-center text-text-muted py-16">
          <p className="text-lg mb-2">Нет проектов</p>
          <p className="text-sm mb-4">
            Создайте проект вручную или добавьте страницу, и проект определится
            автоматически по адресу
          </p>
          <Link
            to="/projects/new"
            className="inline-flex px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/80 transition"
          >
            Создать проект
          </Link>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface-2 text-text-muted">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Название</th>
                <th className="text-left px-4 py-3 font-medium">Адрес</th>
                <th className="text-right px-4 py-3 font-medium">Страниц</th>
                <th className="text-right px-4 py-3 font-medium">Требуют внимания</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((project) => (
                <tr
                  key={project.id}
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="border-t border-border cursor-pointer hover:bg-surface-2/60 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-white">{project.name}</div>
                  </td>
                  <td className="px-4 py-3 text-text-muted">{project.base_url}</td>
                  <td className="px-4 py-3 text-right text-white">{project.pages_count}</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`inline-flex min-w-8 justify-center px-2 py-1 rounded-md text-xs font-medium ${
                        project.attention_count > 0
                          ? "bg-red-500/10 text-red-400"
                          : "bg-green-500/10 text-green-400"
                      }`}
                    >
                      {project.attention_count}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
