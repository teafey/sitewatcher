import axios from "axios";

const API_KEY = localStorage.getItem("sitewatcher_api_key") || "";

const client = axios.create({
  baseURL: "/api",
  headers: {
    "X-API-Key": API_KEY,
  },
});

export function setApiKey(key: string) {
  localStorage.setItem("sitewatcher_api_key", key);
  client.defaults.headers["X-API-Key"] = key;
}

export interface Page {
  id: string;
  url: string;
  name: string | null;
  project_id: string | null;
  viewport_width: number;
  viewport_height: number;
  viewports?: { width: number; height: number }[];
  check_interval_hours: number;
  diff_threshold: number;
  ignore_selectors: string[];
  wait_for_selector: string | null;
  scroll_to_bottom: boolean;
  max_scrolls: number;
  wait_seconds: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Snapshot {
  id: string;
  page_id: string;
  screenshot_path: string | null;
  dom_hash: string | null;
  diff_percent: number | null;
  diff_image_path: string | null;
  has_changes: boolean | null;
  error_message: string | null;
  viewport_width?: number | null;
  viewport_height?: number | null;
  captured_at: string;
}

export interface Stats {
  total_projects: number;
  total_pages: number;
  active_pages: number;
  attention_pages: number;
  last_snapshot_at: string | null;
}

export interface Project {
  id: string;
  name: string;
  base_url: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectRow extends Project {
  pages_count: number;
  attention_count: number;
}

export const api = {
  // Projects
  getProjects: () => client.get<ProjectRow[]>("/projects").then((r) => r.data),
  getProject: (id: string) => client.get<Project>(`/projects/${id}`).then((r) => r.data),
  createProject: (data: { name: string; base_url: string }) =>
    client.post<Project>("/projects", data).then((r) => r.data),
  updateProject: (id: string, data: Partial<Project>) =>
    client.put<Project>(`/projects/${id}`, data).then((r) => r.data),
  getProjectPages: (id: string) =>
    client.get<Page[]>(`/projects/${id}/pages`).then((r) => r.data),

  // Pages
  getPages: () => client.get<Page[]>("/pages").then((r) => r.data),
  getPage: (id: string) => client.get<Page>(`/pages/${id}`).then((r) => r.data),
  createPage: (data: Partial<Page>) =>
    client.post<Page>("/pages", data).then((r) => r.data),
  updatePage: (id: string, data: Partial<Page>) =>
    client.put<Page>(`/pages/${id}`, data).then((r) => r.data),
  deletePage: (id: string) => client.delete(`/pages/${id}`),

  // Snapshots
  getSnapshots: (
    pageId: string,
    params?: {
      limit?: number;
      offset?: number;
      changes_only?: boolean;
      viewport_width?: number;
      viewport_height?: number;
    }
  ) =>
    client
      .get<Snapshot[]>(`/snapshots/${pageId}`, { params })
      .then((r) => r.data),
  getSnapshot: (id: string) =>
    client.get<Snapshot>(`/snapshots/detail/${id}`).then((r) => r.data),
  getScreenshotUrl: (id: string) => `/api/snapshots/detail/${id}/screenshot`,
  getDiffImageUrl: (id: string) => `/api/snapshots/detail/${id}/diff-image`,
  getTextDiff: (id: string) =>
    client
      .get<string>(`/snapshots/detail/${id}/text-diff`)
      .then((r) => r.data),
  deleteSnapshot: (id: string) => client.delete(`/snapshots/detail/${id}`),

  // Stats
  getStats: () => client.get<Stats>("/stats").then((r) => r.data),

  // Actions
  triggerCheck: () => client.post("/check").then((r) => r.data),
  triggerCheckPage: (id: string) =>
    client.post(`/check/${id}`).then((r) => r.data),
};

export default api;
