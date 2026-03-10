import { Routes, Route, Link } from "react-router-dom";
import ProjectsList from "./pages/ProjectsList";
import PagesList from "./pages/PagesList";
import PageDetail from "./pages/PageDetail";
import PageForm from "./pages/PageForm";
import BulkImport from "./pages/BulkImport";
import ProjectForm from "./pages/ProjectForm";

export default function App() {
  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border bg-surface">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-white">
            SiteWatcher
          </Link>
          <nav className="flex gap-4">
            <Link
              to="/"
              className="text-text-dim hover:text-white transition-colors"
            >
              Проекты
            </Link>
            <Link
              to="/projects/new"
              className="text-text-dim hover:text-white transition-colors"
            >
              Создать проект
            </Link>
            <Link
              to="/add"
              className="text-text-dim hover:text-white transition-colors"
            >
              Добавить
            </Link>
            <Link
              to="/import"
              className="text-text-dim hover:text-white transition-colors"
            >
              Импорт
            </Link>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<ProjectsList />} />
          <Route path="/projects/new" element={<ProjectForm />} />
          <Route path="/projects/:projectId" element={<PagesList />} />
          <Route path="/pages/:pageId" element={<PageDetail />} />
          <Route path="/add" element={<PageForm />} />
          <Route path="/projects/:projectId/add" element={<PageForm />} />
          <Route path="/edit/:pageId" element={<PageForm />} />
          <Route path="/import" element={<BulkImport />} />
        </Routes>
      </main>
    </div>
  );
}
