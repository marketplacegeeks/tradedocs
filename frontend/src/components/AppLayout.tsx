// Persistent application shell rendered after login (FR-03).
// Left: collapsible sidebar with role-filtered navigation.
// Right: main content area where page components render.

import { useState } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { Layout, Menu, Button, Typography, Avatar, Flex, Tooltip, message } from "antd";
import {
  FileTextOutlined,
  ContainerOutlined,
  DollarOutlined,
  DatabaseOutlined,
  TeamOutlined,
  UserOutlined,
  BarChartOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from "@ant-design/icons";

import { useAuth } from "../store/AuthContext";
import { logoutUser } from "../api/auth";
import { ROLES } from "../utils/constants";

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

// ---- Nav item definitions -------------------------------------------------
// Each item declares which roles can see it.

const NAV_ITEMS = [
  {
    key: "/proforma-invoices",
    icon: <FileTextOutlined />,
    label: "Proforma Invoice",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN],
  },
  {
    key: "/packing-lists",
    icon: <ContainerOutlined />,
    label: "Packing List",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN],
  },
  {
    key: "/commercial-invoices",
    icon: <DollarOutlined />,
    label: "Commercial Invoice",
    roles: [ROLES.MAKER, ROLES.CHECKER, ROLES.COMPANY_ADMIN],
  },
  {
    key: "/master-data",
    icon: <DatabaseOutlined />,
    label: "Master Data",
    roles: [ROLES.CHECKER, ROLES.COMPANY_ADMIN],
    children: [
      { key: "/master-data/organisations", label: "Organisations" },
      { key: "/master-data/banks", label: "Banks" },
    ],
  },
  {
    key: "/users",
    icon: <TeamOutlined />,
    label: "User Management",
    roles: [ROLES.COMPANY_ADMIN],
  },
  {
    key: "/reports",
    icon: <BarChartOutlined />,
    label: "Reports",
    roles: [ROLES.CHECKER, ROLES.COMPANY_ADMIN],
  },
];

// ---- Component ------------------------------------------------------------

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  // Filter nav items to only those the current user's role can see.
  const visibleItems = NAV_ITEMS.filter(
    (item) => user && item.roles.includes(user.role as typeof ROLES[keyof typeof ROLES])
  ).map((item) => ({
    key: item.key,
    icon: item.icon,
    label: item.label,
    children: item.children,
  }));

  // Determine which menu item is active based on the current URL.
  // For nested items (Master Data), also keep the parent open.
  const selectedKey = location.pathname;
  const openKeys = NAV_ITEMS.filter(
    (item) => item.children?.some((child) => location.pathname.startsWith(child.key))
  ).map((item) => item.key);

  async function handleLogout() {
    try {
      await logoutUser();
    } catch {
      // Even if the server call fails, clear local state and redirect.
    }
    logout();
    navigate("/login");
    message.success("You have been logged out.");
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        trigger={null}
        width={220}
        style={{ background: "#001529" }}
      >
        {/* Logo / app name */}
        <Flex
          align="center"
          justify={collapsed ? "center" : "flex-start"}
          style={{ padding: collapsed ? "16px 0" : "16px 20px", marginBottom: 8 }}
        >
          <Text strong style={{ color: "#fff", fontSize: collapsed ? 14 : 16, whiteSpace: "nowrap" }}>
            {collapsed ? "TD" : "TradeDocs"}
          </Text>
        </Flex>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={openKeys}
          items={visibleItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>

      <Layout>
        <Header
          style={{
            background: "#fff",
            padding: "0 16px",
            borderBottom: "1px solid #f0f0f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          {/* Sidebar collapse toggle */}
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />

          {/* User info + logout */}
          <Flex align="center" gap={12}>
            <Avatar icon={<UserOutlined />} size="small" />
            {user && (
              <Text style={{ fontSize: 13 }}>
                {user.firstName} {user.lastName}
              </Text>
            )}
            <Tooltip title="Log out">
              <Button
                type="text"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
              />
            </Tooltip>
          </Flex>
        </Header>

        <Content style={{ background: "#f5f5f5", overflow: "auto" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
