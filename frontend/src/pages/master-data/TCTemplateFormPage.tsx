// T&C Template create / edit form with TipTap rich text editor (FR-07).
// Supports: Bold, Italic, Underline, Bullet List, Ordered List, Link, Clear Formatting.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Select, message } from "antd";
import { ArrowLeft } from "lucide-react";

// TipTap core and extensions for the required formatting toolbar
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Link from "@tiptap/extension-link";

import {
  getTCTemplate,
  createTCTemplate,
  updateTCTemplate,
} from "../../api/tcTemplates";
import { listOrganisations } from "../../api/organisations";

// ---- Toolbar button component ---------------------------------------------

function ToolbarButton({
  active,
  onClick,
  title,
  children,
}: {
  active?: boolean;
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: 30,
        height: 30,
        borderRadius: 6,
        border: "none",
        cursor: "pointer",
        fontFamily: "var(--font-body)",
        fontSize: 13,
        fontWeight: 600,
        background: active ? "var(--primary-light)" : "transparent",
        color: active ? "var(--primary)" : "var(--text-secondary)",
        transition: "background 0.15s ease",
      }}
      onMouseEnter={(e) => {
        if (!active)
          (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)";
      }}
      onMouseLeave={(e) => {
        if (!active)
          (e.currentTarget as HTMLButtonElement).style.background = "transparent";
      }}
    >
      {children}
    </button>
  );
}

// ---- Main page ------------------------------------------------------------

export default function TCTemplateFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Form field state
  const [name, setName] = useState("");
  const [selectedOrgIds, setSelectedOrgIds] = useState<number[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // TipTap editor instance with the required extensions
  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Link.configure({ openOnClick: false }),
    ],
    content: "",
    editorProps: {
      attributes: {
        style:
          "min-height: 220px; outline: none; font-family: var(--font-body); font-size: 14px; color: var(--text-primary); line-height: 1.7;",
      },
    },
  });

  // Load all active organisations for the multi-select dropdown
  const { data: organisations = [] } = useQuery({
    queryKey: ["organisations"],
    queryFn: () => listOrganisations(),
  });

  // On edit mode: fetch the existing template and pre-fill the form
  const { data: existingTemplate } = useQuery({
    queryKey: ["tc-templates", Number(id)],
    queryFn: () => getTCTemplate(Number(id)),
    enabled: isEditMode,
  });

  // Pre-fill form once the existing template is loaded
  useEffect(() => {
    if (existingTemplate && editor) {
      setName(existingTemplate.name);
      setSelectedOrgIds(existingTemplate.organisations);
      editor.commands.setContent(existingTemplate.body);
    }
  }, [existingTemplate, editor]);

  const createMutation = useMutation({
    mutationFn: createTCTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tc-templates"] });
      message.success("Template created.");
      navigate("/master-data/tc-templates");
    },
    onError: (err: unknown) => handleApiError(err),
  });

  const updateMutation = useMutation({
    mutationFn: ({ payload }: { payload: Parameters<typeof updateTCTemplate>[1] }) =>
      updateTCTemplate(Number(id), payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tc-templates"] });
      queryClient.invalidateQueries({ queryKey: ["tc-templates", Number(id)] });
      message.success("Template updated.");
      navigate("/master-data/tc-templates");
    },
    onError: (err: unknown) => handleApiError(err),
  });

  // Map API validation errors (field: message[]) back onto the form
  function handleApiError(err: unknown) {
    const apiErr = err as { response?: { data?: Record<string, string[]> } };
    if (apiErr?.response?.data) {
      const fieldErrors: Record<string, string> = {};
      for (const [field, messages] of Object.entries(apiErr.response.data)) {
        fieldErrors[field] = Array.isArray(messages) ? messages[0] : String(messages);
      }
      setErrors(fieldErrors);
    } else {
      message.error("Something went wrong. Please try again.");
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const body = editor?.getHTML() ?? "";
    const payload = { name, body, organisations: selectedOrgIds };

    if (isEditMode) {
      updateMutation.mutate({ payload });
    } else {
      createMutation.mutate(payload);
    }
  }

  // Add a link to selected text via window.prompt
  function handleSetLink() {
    if (!editor) return;
    const url = window.prompt("Enter URL:", editor.getAttributes("link").href ?? "https://");
    if (url === null) return; // cancelled
    if (url === "") {
      editor.chain().focus().extendMarkRange("link").unsetLink().run();
    } else {
      editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
    }
  }

  const isSaving = createMutation.isPending || updateMutation.isPending;

  const orgOptions = organisations.map((org) => ({
    label: org.name,
    value: org.id,
  }));

  return (
    <div style={{ maxWidth: 820 }}>
      {/* Back link */}
      <button
        type="button"
        onClick={() => navigate("/master-data/tc-templates")}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 20,
          padding: "5px 0",
          background: "none",
          border: "none",
          cursor: "pointer",
          fontFamily: "var(--font-body)",
          fontSize: 13,
          color: "var(--text-muted)",
        }}
      >
        <ArrowLeft size={14} strokeWidth={1.5} />
        Back to Templates
      </button>

      {/* Page title */}
      <h1
        style={{
          fontFamily: "var(--font-heading)",
          fontSize: 22,
          fontWeight: 700,
          color: "var(--text-primary)",
          marginBottom: 24,
        }}
      >
        {isEditMode ? "Edit Template" : "New T&C Template"}
      </h1>

      {/* Form card */}
      <form onSubmit={handleSubmit}>
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-light)",
            borderRadius: 14,
            boxShadow: "var(--shadow-card)",
            padding: "24px 28px",
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          {/* Template Name */}
          <div>
            <label
              style={{
                display: "block",
                fontFamily: "var(--font-body)",
                fontSize: 12,
                fontWeight: 500,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: 6,
              }}
            >
              Template Name <span style={{ color: "var(--pastel-pink-text)" }}>*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Standard Export Terms"
              style={{
                width: "100%",
                background: "var(--bg-input)",
                border: `1px solid ${errors.name ? "var(--pastel-pink-text)" : "var(--border-medium)"}`,
                borderRadius: 8,
                padding: "9px 14px",
                fontFamily: "var(--font-body)",
                fontSize: 14,
                color: "var(--text-primary)",
                outline: "none",
                boxSizing: "border-box",
              }}
              onFocus={(e) =>
                (e.currentTarget.style.borderColor = errors.name
                  ? "var(--pastel-pink-text)"
                  : "var(--primary)")
              }
              onBlur={(e) =>
                (e.currentTarget.style.borderColor = errors.name
                  ? "var(--pastel-pink-text)"
                  : "var(--border-medium)")
              }
            />
            {errors.name && (
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 12,
                  color: "var(--pastel-pink-text)",
                  marginTop: 4,
                }}
              >
                {errors.name}
              </p>
            )}
          </div>

          {/* Organisation Association */}
          <div>
            <label
              style={{
                display: "block",
                fontFamily: "var(--font-body)",
                fontSize: 12,
                fontWeight: 500,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: 6,
              }}
            >
              Organisations <span style={{ color: "var(--pastel-pink-text)" }}>*</span>
            </label>
            <Select
              mode="multiple"
              allowClear
              style={{ width: "100%" }}
              placeholder="Select organisations this template applies to"
              value={selectedOrgIds}
              onChange={(values: number[]) => setSelectedOrgIds(values)}
              options={orgOptions}
              status={errors.organisations ? "error" : undefined}
            />
            {errors.organisations && (
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 12,
                  color: "var(--pastel-pink-text)",
                  marginTop: 4,
                }}
              >
                {errors.organisations}
              </p>
            )}
          </div>

          {/* Rich Text Body */}
          <div>
            <label
              style={{
                display: "block",
                fontFamily: "var(--font-body)",
                fontSize: 12,
                fontWeight: 500,
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                marginBottom: 6,
              }}
            >
              Terms &amp; Conditions Body <span style={{ color: "var(--pastel-pink-text)" }}>*</span>
            </label>

            {/* Editor container */}
            <div
              style={{
                border: `1px solid ${errors.body ? "var(--pastel-pink-text)" : "var(--border-medium)"}`,
                borderRadius: 8,
                overflow: "hidden",
                background: "var(--bg-surface)",
              }}
            >
              {/* Formatting toolbar */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  padding: "6px 10px",
                  borderBottom: "1px solid var(--border-light)",
                  background: "var(--bg-base)",
                  flexWrap: "wrap",
                }}
              >
                <ToolbarButton
                  title="Bold"
                  active={editor?.isActive("bold")}
                  onClick={() => editor?.chain().focus().toggleBold().run()}
                >
                  <strong>B</strong>
                </ToolbarButton>
                <ToolbarButton
                  title="Italic"
                  active={editor?.isActive("italic")}
                  onClick={() => editor?.chain().focus().toggleItalic().run()}
                >
                  <em>I</em>
                </ToolbarButton>
                <ToolbarButton
                  title="Underline"
                  active={editor?.isActive("underline")}
                  onClick={() => editor?.chain().focus().toggleUnderline().run()}
                >
                  <u>U</u>
                </ToolbarButton>

                {/* Divider */}
                <div
                  style={{
                    width: 1,
                    height: 18,
                    background: "var(--border-light)",
                    margin: "0 4px",
                  }}
                />

                <ToolbarButton
                  title="Bullet List"
                  active={editor?.isActive("bulletList")}
                  onClick={() => editor?.chain().focus().toggleBulletList().run()}
                >
                  ≡
                </ToolbarButton>
                <ToolbarButton
                  title="Numbered List"
                  active={editor?.isActive("orderedList")}
                  onClick={() => editor?.chain().focus().toggleOrderedList().run()}
                >
                  1≡
                </ToolbarButton>

                {/* Divider */}
                <div
                  style={{
                    width: 1,
                    height: 18,
                    background: "var(--border-light)",
                    margin: "0 4px",
                  }}
                />

                <ToolbarButton
                  title="Link"
                  active={editor?.isActive("link")}
                  onClick={handleSetLink}
                >
                  🔗
                </ToolbarButton>
                <ToolbarButton
                  title="Clear Formatting"
                  onClick={() =>
                    editor
                      ?.chain()
                      .focus()
                      .clearNodes()
                      .unsetAllMarks()
                      .run()
                  }
                >
                  Tx
                </ToolbarButton>
              </div>

              {/* Editor content area */}
              <div style={{ padding: "12px 16px" }}>
                <EditorContent editor={editor} />
              </div>
            </div>

            {errors.body && (
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 12,
                  color: "var(--pastel-pink-text)",
                  marginTop: 4,
                }}
              >
                {errors.body}
              </p>
            )}
          </div>
        </div>

        {/* Form actions */}
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 10,
            marginTop: 20,
          }}
        >
          <button
            type="button"
            onClick={() => navigate("/master-data/tc-templates")}
            style={{
              padding: "9px 18px",
              background: "transparent",
              color: "var(--text-secondary)",
              border: "1px solid var(--border-medium)",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            style={{
              padding: "9px 18px",
              background: isSaving ? "var(--border-medium)" : "var(--primary)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontFamily: "var(--font-body)",
              fontSize: 14,
              fontWeight: 500,
              cursor: isSaving ? "not-allowed" : "pointer",
              transition: "background 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (!isSaving)
                (e.currentTarget as HTMLButtonElement).style.background = "var(--primary-hover)";
            }}
            onMouseLeave={(e) => {
              if (!isSaving)
                (e.currentTarget as HTMLButtonElement).style.background = "var(--primary)";
            }}
          >
            {isSaving ? "Saving…" : isEditMode ? "Save Changes" : "Create Template"}
          </button>
        </div>
      </form>
    </div>
  );
}
