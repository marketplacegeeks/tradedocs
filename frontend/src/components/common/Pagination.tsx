// Shared pagination bar used by all list pages.

interface PaginationBarProps {
  currentPage: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export default function PaginationBar({
  currentPage,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
}: PaginationBarProps) {
  const from = totalCount === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const to = Math.min(currentPage * pageSize, totalCount);

  const btnStyle = (disabled: boolean): React.CSSProperties => ({
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    padding: "6px 14px",
    border: "1px solid var(--border-medium)",
    borderRadius: 7,
    background: disabled ? "var(--bg-base)" : "var(--bg-surface)",
    fontFamily: "var(--font-body)",
    fontSize: 13,
    color: disabled ? "var(--text-muted)" : "var(--text-primary)",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.5 : 1,
    transition: "background 0.12s ease",
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 16px",
        borderTop: "1px solid var(--border-light)",
        background: "var(--bg-surface)",
      }}
    >
      <span
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 13,
          color: "var(--text-muted)",
        }}
      >
        {totalCount === 0
          ? "No results"
          : `Showing ${from}–${to} of ${totalCount}`}
      </span>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          style={btnStyle(currentPage <= 1)}
        >
          ← Prev
        </button>

        <span
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 13,
            color: "var(--text-secondary)",
            minWidth: 80,
            textAlign: "center",
          }}
        >
          Page {currentPage} of {totalPages || 1}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          style={btnStyle(currentPage >= totalPages)}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
