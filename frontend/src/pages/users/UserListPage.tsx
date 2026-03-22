// User Management page — Company Admin only (FR-10).
// Lists all users (active + inactive) with inline modals for invite and edit.

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Modal, message, Select } from "antd";
import { UserPlus, Pencil } from "lucide-react";

import { listUsers, createUser, updateUser } from "../../api/users";
import type { User, UserCreatePayload, UserUpdatePayload } from "../../api/users";
import { useAuth } from "../../store/AuthContext";
import { ROLES, COUNTRY_DIAL_CODES } from "../../utils/constants";

// Build a sorted, deduplicated list of dial code options for the phone dropdown.
// e.g. { value: "+91", label: "+91" }
const DIAL_CODE_OPTIONS = Array.from(
  new Set(Object.values(COUNTRY_DIAL_CODES))
)
  .sort()
  .map((code) => ({ value: code, label: code }));

// ---- Role chip styles -------------------------------------------------------

const ROLE_CHIP: Record<string, { bg: string; color: string; label: string }> = {
  [ROLES.COMPANY_ADMIN]: { bg: "var(--pastel-blue)", color: "var(--pastel-blue-text)", label: "Company Admin" },
  [ROLES.CHECKER]:       { bg: "var(--pastel-orange)", color: "var(--pastel-orange-text)", label: "Checker" },
  [ROLES.MAKER]:         { bg: "var(--pastel-green)", color: "var(--pastel-green-text)", label: "Maker" },
};

function RoleChip({ role }: { role: string }) {
  const style = ROLE_CHIP[role] ?? { bg: "var(--bg-hover)", color: "var(--text-secondary)", label: role };
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 20,
        background: style.bg,
        color: style.color,
        fontFamily: "var(--font-body)",
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {style.label}
    </span>
  );
}

function StatusChip({ isActive }: { isActive: boolean }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 20,
        background: isActive ? "var(--pastel-green)" : "var(--pastel-pink)",
        color: isActive ? "var(--pastel-green-text)" : "var(--pastel-pink-text)",
        fontFamily: "var(--font-body)",
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {isActive ? "Active" : "Inactive"}
    </span>
  );
}

// ---- Shared field style helper ----------------------------------------------

function fieldLabel(label: string) {
  return (
    <div
      style={{
        fontFamily: "var(--font-body)",
        fontSize: 13,
        fontWeight: 500,
        color: "var(--text-secondary)",
        marginBottom: 4,
      }}
    >
      {label}
    </div>
  );
}

function textInput(
  value: string,
  onChange: (v: string) => void,
  placeholder?: string,
  type = "text"
) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: "100%",
        padding: "8px 12px",
        borderRadius: 8,
        border: "1px solid var(--border-medium)",
        fontFamily: "var(--font-body)",
        fontSize: 14,
        color: "var(--text-primary)",
        background: "var(--bg-surface)",
        boxSizing: "border-box",
        outline: "none",
      }}
    />
  );
}

// ---- Main page component ---------------------------------------------------

export default function UserListPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();

  // ---- Invite modal state
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteForm, setInviteForm] = useState<UserCreatePayload>({
    email: "", first_name: "", last_name: "", role: ROLES.MAKER, password: "",
  });
  const [inviteErrors, setInviteErrors] = useState<Partial<UserCreatePayload>>({});

  // ---- Edit modal state
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState<UserUpdatePayload>({});
  const [editPhoneError, setEditPhoneError] = useState<string | null>(null);

  // ---- Data
  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
  });

  // ---- Mutations
  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      message.success("User created successfully.");
      setInviteOpen(false);
      setInviteForm({ email: "", first_name: "", last_name: "", role: ROLES.MAKER, password: "" });
      setInviteErrors({});
    },
    onError: (err: unknown) => {
      // Map API validation errors back to fields.
      const apiErrors = (err as { response?: { data?: Record<string, string[]> } })
        ?.response?.data;
      if (apiErrors) {
        setInviteErrors({
          email: apiErrors.email?.[0],
          first_name: apiErrors.first_name?.[0],
          last_name: apiErrors.last_name?.[0],
          password: apiErrors.password?.[0],
        } as Partial<UserCreatePayload>);
      } else {
        message.error("Failed to create user. Please try again.");
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UserUpdatePayload }) =>
      updateUser(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      message.success("User updated successfully.");
      setEditingUser(null);
      setEditPhoneError(null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[]> } })
        ?.response?.data;
      if (detail?.phone) {
        setEditPhoneError(Array.isArray(detail.phone) ? detail.phone[0] : String(detail.phone));
      } else if (detail?.role) {
        message.error(detail.role[0]);
      } else if (detail?.is_active) {
        message.error(detail.is_active[0]);
      } else {
        message.error("Failed to update user. Please try again.");
      }
    },
  });

  // ---- Open edit modal for a user
  function openEdit(u: User) {
    setEditingUser(u);
    setEditForm({
      role: u.role,
      is_active: u.is_active,
      phone_country_code: u.phone_country_code ?? "",
      phone_number: u.phone_number ?? "",
    });
    setEditPhoneError(null);
  }

  // ---- Determine which roles are allowed in the edit dropdown
  // Company Admin cannot be assigned to another user via this form —
  // only Maker and Checker are selectable. (Admins are created manually.)
  // If editing a Company Admin, their role shows but cannot be changed (self-guard on backend).
  const editableRoles = editingUser?.role === ROLES.COMPANY_ADMIN
    ? [{ value: ROLES.COMPANY_ADMIN, label: "Company Admin" }]
    : [
        { value: ROLES.MAKER, label: "Maker" },
        { value: ROLES.CHECKER, label: "Checker" },
      ];

  const isEditingSelf = editingUser?.id === currentUser?.id;

  return (
    <div>
      {/* Page header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}
          >
            User Management
          </h1>
          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: "var(--text-muted)" }}>
            {users.length} user{users.length !== 1 ? "s" : ""}
          </p>
        </div>

        <button
          onClick={() => setInviteOpen(true)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "9px 16px",
            background: "var(--primary)",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            fontFamily: "var(--font-body)",
            fontSize: 14,
            fontWeight: 500,
            cursor: "pointer",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary-hover)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLButtonElement).style.background = "var(--primary)")
          }
        >
          <UserPlus size={16} strokeWidth={2} />
          Invite User
        </button>
      </div>

      {/* Table card */}
      <div
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-light)",
          borderRadius: 14,
          boxShadow: "var(--shadow-card)",
          overflow: "hidden",
        }}
      >
        {isLoading ? (
          <div
            style={{
              padding: 40,
              textAlign: "center",
              color: "var(--text-muted)",
              fontFamily: "var(--font-body)",
            }}
          >
            Loading…
          </div>
        ) : users.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "48px 24px",
              gap: 12,
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-heading)",
                fontSize: 15,
                fontWeight: 600,
                color: "var(--text-primary)",
                margin: 0,
              }}
            >
              No users yet
            </p>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 13,
                color: "var(--text-muted)",
                margin: 0,
              }}
            >
              Click "Invite User" to add the first user.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
              <thead>
                <tr style={{ background: "var(--bg-base)" }}>
                  {["Name", "Email", "Role", "Status", "Joined"].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "12px 16px",
                        textAlign: "left",
                        fontFamily: "var(--font-body)",
                        fontSize: 11,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        color: "var(--text-muted)",
                        borderBottom: "1px solid var(--border-light)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                  <th style={{ padding: "12px 16px", borderBottom: "1px solid var(--border-light)" }} />
                </tr>
              </thead>
              <tbody>
                {users.map((u: User) => (
                  <tr
                    key={u.id}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "var(--bg-hover)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLTableRowElement).style.background = "transparent";
                    }}
                  >
                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-body)",
                          fontSize: 14,
                          fontWeight: 500,
                          color: "var(--text-primary)",
                        }}
                      >
                        {u.full_name}
                      </span>
                    </td>

                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <span
                        style={{
                          fontFamily: "var(--font-body)",
                          fontSize: 13,
                          color: "var(--text-secondary)",
                        }}
                      >
                        {u.email}
                      </span>
                    </td>

                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <RoleChip role={u.role} />
                    </td>

                    <td style={{ padding: "14px 16px", borderBottom: "1px solid var(--border-light)" }}>
                      <StatusChip isActive={u.is_active} />
                    </td>

                    <td
                      style={{
                        padding: "14px 16px",
                        borderBottom: "1px solid var(--border-light)",
                        fontFamily: "var(--font-body)",
                        fontSize: 13,
                        color: "var(--text-muted)",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {new Date(u.date_joined).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>

                    <td
                      style={{
                        padding: "14px 16px",
                        borderBottom: "1px solid var(--border-light)",
                        textAlign: "right",
                      }}
                    >
                      <button
                        onClick={() => openEdit(u)}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: 4,
                          padding: "5px 10px",
                          background: "transparent",
                          border: "1px solid var(--border-medium)",
                          borderRadius: 6,
                          fontFamily: "var(--font-body)",
                          fontSize: 12,
                          fontWeight: 500,
                          color: "var(--text-secondary)",
                          cursor: "pointer",
                        }}
                        onMouseEnter={(e) =>
                          ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")
                        }
                        onMouseLeave={(e) =>
                          ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                        }
                      >
                        <Pencil size={12} strokeWidth={1.5} />
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ---- Invite User Modal ---- */}
      <Modal
        title={
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: 16 }}>
            Invite User
          </span>
        }
        open={inviteOpen}
        onOk={() => createMutation.mutate(inviteForm)}
        onCancel={() => {
          setInviteOpen(false);
          setInviteErrors({});
          setInviteForm({ email: "", first_name: "", last_name: "", role: ROLES.MAKER, password: "" });
        }}
        okText="Create User"
        okButtonProps={{ loading: createMutation.isPending }}
        cancelText="Cancel"
        width={480}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingTop: 8 }}>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              {fieldLabel("First Name")}
              {textInput(inviteForm.first_name, (v) => setInviteForm((f) => ({ ...f, first_name: v })), "First name")}
              {inviteErrors.first_name && (
                <div style={{ color: "var(--error)", fontSize: 12, marginTop: 4 }}>
                  {inviteErrors.first_name}
                </div>
              )}
            </div>
            <div style={{ flex: 1 }}>
              {fieldLabel("Last Name")}
              {textInput(inviteForm.last_name, (v) => setInviteForm((f) => ({ ...f, last_name: v })), "Last name")}
              {inviteErrors.last_name && (
                <div style={{ color: "var(--error)", fontSize: 12, marginTop: 4 }}>
                  {inviteErrors.last_name}
                </div>
              )}
            </div>
          </div>

          <div>
            {fieldLabel("Email")}
            {textInput(inviteForm.email, (v) => setInviteForm((f) => ({ ...f, email: v })), "user@company.com", "email")}
            {inviteErrors.email && (
              <div style={{ color: "var(--error)", fontSize: 12, marginTop: 4 }}>
                {inviteErrors.email}
              </div>
            )}
          </div>

          <div>
            {fieldLabel("Role")}
            <Select
              value={inviteForm.role}
              onChange={(v) => setInviteForm((f) => ({ ...f, role: v }))}
              style={{ width: "100%" }}
              options={[
                { value: ROLES.MAKER, label: "Maker" },
                { value: ROLES.CHECKER, label: "Checker" },
              ]}
            />
          </div>

          <div>
            {fieldLabel("Password")}
            {textInput(inviteForm.password, (v) => setInviteForm((f) => ({ ...f, password: v })), "Min 8 characters", "password")}
            {inviteErrors.password && (
              <div style={{ color: "var(--error)", fontSize: 12, marginTop: 4 }}>
                {inviteErrors.password}
              </div>
            )}
          </div>
        </div>
      </Modal>

      {/* ---- Edit User Modal ---- */}
      <Modal
        title={
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: 16 }}>
            Edit User — {editingUser?.full_name}
          </span>
        }
        open={editingUser !== null}
        onOk={() => {
          if (editingUser) updateMutation.mutate({ id: editingUser.id, payload: editForm });
        }}
        onCancel={() => { setEditingUser(null); setEditPhoneError(null); }}
        okText="Save Changes"
        okButtonProps={{ loading: updateMutation.isPending }}
        cancelText="Cancel"
        width={400}
      >
        {editingUser && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingTop: 8 }}>
            <div>
              {fieldLabel("Role")}
              <Select
                value={editForm.role}
                onChange={(v) => setEditForm((f) => ({ ...f, role: v }))}
                style={{ width: "100%" }}
                options={editableRoles}
                // Company Admins cannot change their own role (enforced on backend too).
                disabled={isEditingSelf && editingUser.role === ROLES.COMPANY_ADMIN}
              />
              {isEditingSelf && editingUser.role === ROLES.COMPANY_ADMIN && (
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                  You cannot change your own role.
                </div>
              )}
            </div>

            <div>
              {fieldLabel("Status")}
              <Select
                value={editForm.is_active}
                onChange={(v) => setEditForm((f) => ({ ...f, is_active: v }))}
                style={{ width: "100%" }}
                options={[
                  { value: true, label: "Active" },
                  { value: false, label: "Inactive" },
                ]}
                // Company Admins cannot deactivate themselves (enforced on backend too).
                disabled={isEditingSelf}
              />
              {isEditingSelf && (
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                  You cannot deactivate your own account.
                </div>
              )}
            </div>

            <div>
              {fieldLabel("Phone Number (optional)")}
              <div style={{ display: "flex", gap: 8 }}>
                <Select
                  value={editForm.phone_country_code || undefined}
                  onChange={(v) => setEditForm((f) => ({ ...f, phone_country_code: v ?? "" }))}
                  allowClear
                  showSearch
                  placeholder="+91"
                  style={{ width: 100, flexShrink: 0 }}
                  options={DIAL_CODE_OPTIONS}
                  filterOption={(input, option) =>
                    (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
                  }
                />
                {textInput(
                  editForm.phone_number ?? "",
                  (v) => setEditForm((f) => ({ ...f, phone_number: v })),
                  "Local number"
                )}
              </div>
              {editPhoneError && (
                <div style={{ color: "var(--error)", fontSize: 12, marginTop: 4 }}>
                  {editPhoneError}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
