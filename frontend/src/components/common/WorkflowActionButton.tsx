// Constraint #24: centralised component for all workflow action buttons.
// Takes documentStatus, userRole, documentType as props.
// Never repeat role+status logic in individual pages.

import { useState } from "react";
import { Modal, Input, message } from "antd";
import { CheckCircle, RotateCcw, XCircle, Send } from "lucide-react";

import { DOCUMENT_STATUS, ROLES } from "../../utils/constants";
import type { DocumentStatus, Role } from "../../utils/constants";

interface WorkflowActionButtonProps {
  documentId: number;
  documentStatus: DocumentStatus | string;
  userRole: Role | string;
  documentType: "proforma_invoice" | "packing_list" | "commercial_invoice";
  /** Called after a successful transition with the new status. */
  onSuccess: (newStatus: string) => void;
  /** Must return a promise that posts to the workflow endpoint. */
  onAction: (action: string, comment: string) => Promise<{ status: string }>;
}

type ActionDef = {
  key: string;
  label: string;
  icon: React.ReactNode;
  variant: "primary" | "success" | "warning" | "danger";
  needsComment: boolean;
  commentLabel?: string;
};

// ---- Role + state → allowed actions map -----------------------------------

function getAllowedActions(status: string, role: string, docType: string): ActionDef[] {
  const actions: ActionDef[] = [];

  const isMakerOrAdmin = role === ROLES.MAKER || role === ROLES.COMPANY_ADMIN;
  const isCheckerOrAdmin = role === ROLES.CHECKER || role === ROLES.COMPANY_ADMIN;

  if (status === DOCUMENT_STATUS.DRAFT && isMakerOrAdmin) {
    actions.push({
      key: "SUBMIT",
      label: "Submit for Approval",
      icon: <Send size={14} strokeWidth={1.5} />,
      variant: "primary",
      needsComment: false,
    });
  }

  if (status === DOCUMENT_STATUS.REWORK && isMakerOrAdmin) {
    actions.push({
      key: "SUBMIT",
      label: "Resubmit",
      icon: <Send size={14} strokeWidth={1.5} />,
      variant: "primary",
      needsComment: false,
    });
  }

  if (status === DOCUMENT_STATUS.PENDING_APPROVAL && isCheckerOrAdmin) {
    actions.push({
      key: "APPROVE",
      label: "Approve",
      icon: <CheckCircle size={14} strokeWidth={1.5} />,
      variant: "success",
      needsComment: false,
    });
    actions.push({
      key: "REWORK",
      label: "Send for Rework",
      icon: <RotateCcw size={14} strokeWidth={1.5} />,
      variant: "warning",
      needsComment: true,
      commentLabel: "Reason for rework (required)",
    });
  }

  // FR-08.1: Permanently Reject is available from ANY state except Permanently Rejected.
  const terminalStates = [DOCUMENT_STATUS.PERMANENTLY_REJECTED];
  if (!terminalStates.includes(status as DocumentStatus) && isCheckerOrAdmin) {
    actions.push({
      key: "PERMANENTLY_REJECT",
      label: "Permanently Reject",
      icon: <XCircle size={14} strokeWidth={1.5} />,
      variant: "danger",
      needsComment: true,
      commentLabel: "Reason for permanent rejection (required)",
    });
  }

  return actions;
}

// ---- Button style helpers --------------------------------------------------

function btnStyle(variant: ActionDef["variant"], disabled: boolean): React.CSSProperties {
  const base: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "8px 16px",
    borderRadius: 8,
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "var(--font-body)",
    fontSize: 13,
    fontWeight: 500,
    opacity: disabled ? 0.6 : 1,
    transition: "background 0.15s ease",
  };
  const colors: Record<ActionDef["variant"], React.CSSProperties> = {
    primary: { background: "var(--primary)", color: "#fff" },
    success: { background: "var(--pastel-green)", color: "var(--pastel-green-text)" },
    warning: { background: "var(--pastel-yellow)", color: "var(--pastel-yellow-text)" },
    danger: { background: "var(--pastel-pink)", color: "var(--pastel-pink-text)" },
  };
  return { ...base, ...colors[variant] };
}

// ---- Component -------------------------------------------------------------

export default function WorkflowActionButton({
  documentId,
  documentStatus,
  userRole,
  documentType,
  onSuccess,
  onAction,
}: WorkflowActionButtonProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [modalAction, setModalAction] = useState<ActionDef | null>(null);
  const [comment, setComment] = useState("");

  const allowedActions = getAllowedActions(documentStatus, userRole, documentType);

  if (allowedActions.length === 0) return null;

  async function handleDirectAction(action: ActionDef) {
    setLoading(action.key);
    try {
      const result = await onAction(action.key, "");
      message.success(`Document ${action.label.toLowerCase()} successfully.`);
      onSuccess(result.status);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.response?.data?.action || "Action failed.";
      message.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(null);
    }
  }

  async function handleCommentAction() {
    if (!modalAction) return;
    if (!comment.trim()) {
      message.error("A comment is required for this action.");
      return;
    }
    setLoading(modalAction.key);
    try {
      const result = await onAction(modalAction.key, comment);
      message.success(`Document ${modalAction.label.toLowerCase()} successfully.`);
      setModalAction(null);
      setComment("");
      onSuccess(result.status);
    } catch (err: any) {
      const detail = err?.response?.data?.comment || err?.response?.data?.detail || "Action failed.";
      message.error(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(null);
    }
  }

  return (
    <>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {allowedActions.map((action) => (
          <button
            key={action.key}
            style={btnStyle(action.variant, loading !== null)}
            disabled={loading !== null}
            onClick={() => {
              if (action.needsComment) {
                setModalAction(action);
                setComment("");
              } else {
                handleDirectAction(action);
              }
            }}
          >
            {action.icon}
            {loading === action.key ? "Processing…" : action.label}
          </button>
        ))}
      </div>

      {/* Comment modal for actions that require a comment */}
      <Modal
        title={modalAction?.label}
        open={modalAction !== null}
        onOk={handleCommentAction}
        onCancel={() => {
          setModalAction(null);
          setComment("");
        }}
        okText="Confirm"
        okButtonProps={{ loading: loading !== null }}
        destroyOnClose
      >
        <p style={{ marginBottom: 12, fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-secondary)" }}>
          {modalAction?.commentLabel}
        </p>
        <Input.TextArea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={4}
          placeholder="Enter your comment…"
          autoFocus
        />
      </Modal>
    </>
  );
}
