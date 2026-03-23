// Persistent application shell (FR-03).
// White sidebar (220px), sticky top bar, main content on --bg-base.
// Follows LoopAI design system: Plus Jakarta Sans headings, DM Sans body,
// pastel accent chips, white cards, subtle shadows.

import { useState } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { Dropdown, message } from "antd";
import {
  FileText, Package, Database, Users, BarChart2,
  Building2, LogOut, ChevronDown, Menu, X, ChevronsLeft, ShoppingBag,
} from "lucide-react";

import { useAuth } from "../store/AuthContext";
import { logoutUser } from "../api/auth";
import { ROLES } from "../utils/constants";

// ---- Nav configuration ----------------------------------------------------

const NAV_ITEMS = [
  {
    key: "/proforma-invoices",
    icon: FileText,
    label: "Proforma Invoice",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
  },
  {
    key: "/packing-lists",
    icon: Package,
    label: "P.List & C. Invoice",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
  },
  {
    key: "/purchase-orders",
    icon: ShoppingBag,
    label: "Purchase Order",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
  },
  {
    key: "/master-data",
    icon: Database,
    label: "Master Data",
    roles: [ROLES.CHECKER, ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
    children: [
      { key: "/master-data/organisations", label: "Organisations" },
      { key: "/master-data/banks", label: "Banks" },
      { key: "/master-data/tc-templates", label: "T&C Templates" },
      { key: "/master-data/reference-data", label: "Reference Data" },
    ],
  },
  {
    key: "/users",
    icon: Users,
    label: "User Management",
    roles: [ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
  },
  {
    key: "/reports",
    icon: BarChart2,
    label: "Reports",
    roles: [ROLES.CHECKER, ROLES.COMPANY_ADMIN, ROLES.SUPER_ADMIN],
  },
];

// ---- Sidebar nav item component -------------------------------------------

function NavItem({
  item,
  isActive,
  isChildActive,
  collapsed,
  isOpen,
  onToggle,
  onNavigate,
}: {
  item: typeof NAV_ITEMS[0];
  isActive: boolean;
  isChildActive: boolean;
  collapsed: boolean;
  isOpen: boolean;
  onToggle: () => void;
  onNavigate: (key: string) => void;
}) {
  const Icon = item.icon;
  const active = isActive || isChildActive;

  return (
    <div>
      <button
        onClick={() => (item.children ? onToggle() : onNavigate(item.key))}
        style={{
          display: "flex",
          alignItems: "center",
          width: "100%",
          gap: 10,
          padding: collapsed ? "10px 0" : "9px 12px",
          justifyContent: collapsed ? "center" : "flex-start",
          borderRadius: 8,
          border: "none",
          cursor: "pointer",
          fontFamily: "var(--font-body)",
          fontSize: 14,
          fontWeight: active ? 600 : 400,
          color: active ? "var(--primary)" : "var(--text-secondary)",
          background: active ? "var(--primary-light)" : "transparent",
          transition: "all 0.15s ease",
          marginBottom: 2,
        }}
        onMouseEnter={(e) => {
          if (!active) (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)";
        }}
        onMouseLeave={(e) => {
          if (!active) (e.currentTarget as HTMLButtonElement).style.background = "transparent";
        }}
      >
        <Icon size={18} strokeWidth={1.5} style={{ flexShrink: 0 }} />
        {!collapsed && (
          <>
            <span style={{ flex: 1, textAlign: "left" }}>{item.label}</span>
            {item.children && (
              <ChevronDown
                size={14}
                strokeWidth={2}
                style={{
                  transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.2s ease",
                  color: "var(--text-muted)",
                }}
              />
            )}
          </>
        )}
      </button>

      {/* Child items */}
      {!collapsed && item.children && isOpen && (
        <div style={{ paddingLeft: 28, marginBottom: 4 }}>
          {item.children.map((child) => {
            const childActive = isActive && window.location.pathname === child.key;
            return (
              <button
                key={child.key}
                onClick={() => onNavigate(child.key)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "7px 12px",
                  borderRadius: 6,
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "var(--font-body)",
                  fontSize: 13,
                  fontWeight: childActive ? 600 : 400,
                  color: childActive ? "var(--primary)" : "var(--text-secondary)",
                  background: childActive ? "var(--primary-light)" : "transparent",
                  marginBottom: 1,
                }}
                onMouseEnter={(e) => {
                  if (!childActive) (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)";
                }}
                onMouseLeave={(e) => {
                  if (!childActive) (e.currentTarget as HTMLButtonElement).style.background = childActive ? "var(--primary-light)" : "transparent";
                }}
              >
                {child.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ---- Main layout ----------------------------------------------------------

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openGroups, setOpenGroups] = useState<string[]>(["/master-data"]);

  const visibleItems = NAV_ITEMS.filter(
    (item) => user && item.roles.includes(user.role as typeof ROLES[keyof typeof ROLES])
  );

  function isItemActive(item: typeof NAV_ITEMS[0]) {
    if (item.children) {
      return item.children.some((c) => location.pathname.startsWith(c.key));
    }
    return location.pathname === item.key;
  }

  function toggleGroup(key: string) {
    setOpenGroups((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }

  async function handleLogout() {
    try {
      await logoutUser();
    } catch {
      // Clear local state regardless
    }
    logout();
    navigate("/login");
    message.success("You've been logged out.");
  }

  const userInitials = user
    ? `${user.firstName?.[0] ?? ""}${user.lastName?.[0] ?? ""}`.toUpperCase() || "U"
    : "U";

  const sidebarContent = (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--bg-sidebar)",
        borderRight: "1px solid var(--border-light)",
        width: collapsed ? 64 : 220,
        transition: "width 0.2s ease",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div
        style={{
          padding: collapsed ? "20px 0" : "20px 20px 16px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          justifyContent: collapsed ? "center" : "flex-start",
          borderBottom: "1px solid var(--border-light)",
          marginBottom: 12,
        }}
      >
        <Building2 size={22} strokeWidth={2} color="var(--primary)" style={{ flexShrink: 0 }} />
        {!collapsed && (
          <span
            style={{
              fontFamily: "var(--font-heading)",
              fontWeight: 700,
              fontSize: 16,
              color: "var(--text-primary)",
              whiteSpace: "nowrap",
            }}
          >
            TradeDocs
          </span>
        )}
      </div>

      {/* Nav items */}
      <div style={{ flex: 1, padding: collapsed ? "0 8px" : "0 12px", overflowY: "auto" }}>
        {visibleItems.map((item) => (
          <NavItem
            key={item.key}
            item={item}
            isActive={isItemActive(item)}
            isChildActive={false}
            collapsed={collapsed}
            isOpen={openGroups.includes(item.key)}
            onToggle={() => toggleGroup(item.key)}
            onNavigate={(key) => {
              navigate(key);
              setMobileOpen(false);
            }}
          />
        ))}
      </div>

      {/* User section at bottom */}
      <div
        style={{
          padding: collapsed ? "12px 8px" : "12px 12px",
          borderTop: "1px solid var(--border-light)",
        }}
      >
        <Dropdown
          menu={{
            items: [
              {
                key: "logout",
                icon: <LogOut size={14} strokeWidth={1.5} />,
                label: "Log out",
                onClick: handleLogout,
                danger: true,
              },
            ],
          }}
          placement="topLeft"
          trigger={["click"]}
        >
          <button
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "100%",
              padding: "8px 10px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              background: "transparent",
              justifyContent: collapsed ? "center" : "flex-start",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
            }
          >
            {/* Avatar */}
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "var(--pastel-blue)",
                color: "var(--pastel-blue-text)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "var(--font-heading)",
                fontSize: 12,
                fontWeight: 700,
                flexShrink: 0,
              }}
            >
              {userInitials}
            </div>
            {!collapsed && user && (
              <div style={{ flex: 1, textAlign: "left", overflow: "hidden" }}>
                <div
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 13,
                    fontWeight: 500,
                    color: "var(--text-primary)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {user.firstName} {user.lastName}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 11,
                    color: "var(--text-muted)",
                  }}
                >
                  {user.role.replace(/_/g, " ")}
                </div>
              </div>
            )}
          </button>
        </Dropdown>
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg-base)" }}>

      {/* Sidebar — desktop */}
      <div style={{ display: "flex" as const, flexShrink: 0 }} className="sidebar-desktop">
        {sidebarContent}
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.35)",
            zIndex: 199,
            display: "none",
          }}
          className="mobile-overlay"
        />
      )}

      {/* Main area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Top bar */}
        <div
          style={{
            height: 56,
            background: "var(--bg-surface)",
            borderBottom: "1px solid var(--border-light)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 32,
              height: 32,
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              background: "transparent",
              color: "var(--text-muted)",
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "var(--bg-hover)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
            }
          >
            {collapsed
              ? <Menu size={18} strokeWidth={1.5} />
              : <ChevronsLeft size={18} strokeWidth={1.5} />
            }
          </button>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            style={{ display: "none" }}
            className="mobile-hamburger"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflow: "auto", padding: 28 }}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
