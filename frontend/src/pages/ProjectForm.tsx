import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

export default function ProjectForm() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const project = await api.createProject({ name, base_url: baseUrl });
      navigate(`/projects/${project.id}`);
    } catch (err) {
      console.error("Project save failed:", err);
      alert("Не удалось создать проект");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl font-bold mb-6">Создать проект</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Название *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            placeholder="Example"
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-dim mb-2">
            Базовый адрес *
          </label>
          <input
            type="url"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            required
            placeholder="https://example.com"
            className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-white placeholder-text-muted focus:outline-none focus:border-accent"
          />
          <p className="text-xs text-text-muted mt-1">
            Проект будет автоматически связываться с новыми страницами этого домена
          </p>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 bg-accent text-white rounded-lg hover:bg-accent/80 transition disabled:opacity-50"
          >
            {saving ? "Сохранение..." : "Создать проект"}
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
