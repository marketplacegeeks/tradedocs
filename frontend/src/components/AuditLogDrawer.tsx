/**
 * AuditLogDrawer — shared audit trail drawer used on PI and PL+CI detail pages.
 *
 * Renders each AuditLog entry as a timeline row with:
 *  - Pastel status chip (to_status) on the left
 *  - Formatted timestamp on the right
 *  - Actor name below, with italic comment if present
 *
 * Design system: pastel chips, DM Sans body, Plus Jakarta Sans for heading.
 * Constraint #23: status strings come from constants.ts.
 */

import { Drawer, Spin } from "antd";
import { History } from "lucide-react";
import { DOCUMENT_STATUS_CHIP, WORKFLOW_ACTION_LABELS } from "../utils/constants";

export interface AuditLogEntry {
  id: number;
  action: string;
  from_status: string;
  to_status: string;
  comment: string;
  performed_by_name: string;
  performed_at: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  entries: AuditLogEntry[];
  loading?: boolean;
  /** Display title — defaults to "Audit Trail" */
  title?: string;
}

export default function AuditLogDrawer({
  open,
  onClose,
  entries,
  loading = false,
  title = "Audit Trail",
}: Props) {
  return (
    <Drawer
      title={
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 600,
            fontSize: 15,
            color: "var(--text-primary)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <History size={16} strokeWidth={1.5} style={{ color: "var(--text-muted)" }} />
          {title}
        </span>
      }
      open={open}
      onClose={onClose}
      width={420}
      styles={{
        body: { padding: "20px 24px" },
        header: { borderBottom: "1px solid var(--border-light)" },
      }}
    >
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", paddingTop: 40 }}>
          <Spin />
        </div>
      ) : entries.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            paddingTop: 48,
            color: "var(--text-muted)",
            fontFamily: "var(--font-body)",
            fontSize: 13,
          }}
        >
          No activity recorded yet.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          {entries.map((entry, idx) => (
            <div
              key={entry.id}
              style={{
                paddingBottom: 16,
                marginBottom: 16,
                borderBottom:
                  idx < entries.length - 1
                    ? "1px solid var(--border-light)"
                    : "none",
              }}
            >
              {/* Row 1: action chip + timestamp */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 6,
                }}
              >
                <span
                  className={DOCUMENT_STATUS_CHIP[entry.to_status] ?? "chip-blue"}
                  style={{ fontSize: 11, fontWeight: 600 }}
                >
                  {WORKFLOW_ACTION_LABELS[entry.action] ?? entry.action}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  {new Date(entry.performed_at).toLocaleString()}
                </span>
              </div>

              {/* Row 2: status transition + actor */}
              <p
                style={{
                  margin: 0,
                  fontFamily: "var(--font-body)",
                  fontSize: 12,
                  color: "var(--text-secondary)",
                }}
              >
                by {entry.performed_by_name ?? "—"}
              </p>

              {/* Row 3: comment (only when present) */}
              {entry.comment && (
                <p
                  style={{
                    margin: "4px 0 0",
                    fontFamily: "var(--font-body)",
                    fontSize: 12,
                    color: "var(--text-secondary)",
                    fontStyle: "italic",
                  }}
                >
                  "{entry.comment}"
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </Drawer>
  );
}
