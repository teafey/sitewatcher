interface Props {
  diff: string;
}

export default function TextDiff({ diff }: Props) {
  if (!diff) return null;

  const lines = diff.split("\n");

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="text-xs text-text-muted px-4 py-2 border-b border-border font-mono">
        Текстовый diff (unified)
      </div>
      <pre className="p-4 overflow-x-auto text-xs font-mono leading-relaxed">
        {lines.map((line, i) => {
          let className = "text-text-dim";
          if (line.startsWith("+") && !line.startsWith("+++")) {
            className = "text-green-600 dark:text-green-400 bg-green-500/10";
          } else if (line.startsWith("-") && !line.startsWith("---")) {
            className = "text-red-600 dark:text-red-400 bg-red-500/10";
          } else if (line.startsWith("@@")) {
            className = "text-accent-light";
          }

          return (
            <div key={i} className={`${className} px-2 -mx-2`}>
              <span className="text-text-muted w-8 inline-block text-right mr-3 select-none">
                {i + 1}
              </span>
              {line}
            </div>
          );
        })}
      </pre>
    </div>
  );
}
