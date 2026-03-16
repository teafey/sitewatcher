import { Routes, Route, Link } from "react-router-dom";
import ProjectsList from "./pages/ProjectsList";
import PagesList from "./pages/PagesList";
import PageDetail from "./pages/PageDetail";
import PageForm from "./pages/PageForm";
import BulkImport from "./pages/BulkImport";
import ProjectForm from "./pages/ProjectForm";
import { useTheme } from "./context/ThemeContext";

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg text-text-dim hover:text-text-primary hover:bg-surface-2 transition-colors"
      title={theme === "dark" ? "Светлая тема" : "Тёмная тема"}
    >
      {theme === "dark" ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
        </svg>
      )}
    </button>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-border bg-surface">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-text-primary">
            SiteWatcher
          </Link>
          <nav className="flex items-center gap-4">
            <Link
              to="/"
              className="text-text-dim hover:text-text-primary transition-colors"
            >
              Проекты
            </Link>
            <Link
              to="/projects/new"
              className="text-text-dim hover:text-text-primary transition-colors"
            >
              Создать проект
            </Link>
            <Link
              to="/add"
              className="text-text-dim hover:text-text-primary transition-colors"
            >
              Добавить
            </Link>
            <Link
              to="/import"
              className="text-text-dim hover:text-text-primary transition-colors"
            >
              Импорт
            </Link>
            <ThemeToggle />
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
