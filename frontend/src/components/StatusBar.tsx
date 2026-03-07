import { useEffect, useState } from "react";
import api, { type Stats } from "../api/client";

export default function StatusBar() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    api.getStats().then(setStats).catch(console.error);
  }, []);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      <StatCard label="Всего страниц" value={stats.total_pages} />
      <StatCard label="Активных" value={stats.active_pages} color="text-green-400" />
      <StatCard
        label="С ошибками"
        value={stats.total_pages - stats.active_pages}
        color="text-red-400"
      />
      <StatCard
        label="Последний снимок"
        value={
          stats.last_snapshot_at
            ? new Date(stats.last_snapshot_at).toLocaleString("ru")
            : "—"
        }
        small
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "text-white",
  small = false,
}: {
  label: string;
  value: string | number;
  color?: string;
  small?: boolean;
}) {
  return (
    <div className="bg-surface border border-border rounded-xl p-4 text-center">
      <div className="text-[11px] uppercase tracking-wider text-text-muted mb-1">
        {label}
      </div>
      <div className={`${small ? "text-sm" : "text-xl"} font-bold ${color}`}>
        {value}
      </div>
    </div>
  );
}
