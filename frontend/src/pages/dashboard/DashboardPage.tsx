// Dashboard placeholder page — shown immediately after login.
// Will be expanded with summary stats and recent document activity in a future sprint.

import { Typography, Card, Row, Col } from "antd";
import { FileTextOutlined, ContainerOutlined, DollarOutlined } from "@ant-design/icons";
import { useAuth } from "../../store/AuthContext";

const { Title, Text } = Typography;

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div style={{ padding: 24 }}>
      <Title level={3} style={{ marginBottom: 4 }}>
        Welcome back{user?.firstName ? `, ${user.firstName}` : ""}
      </Title>
      <Text type="secondary" style={{ display: "block", marginBottom: 32 }}>
        Here's what's happening with your trade documents.
      </Text>

      <Row gutter={16}>
        <Col xs={24} sm={8}>
          <Card>
            <FileTextOutlined style={{ fontSize: 28, color: "#1677ff", marginBottom: 8 }} />
            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
              Proforma Invoices
            </Title>
            <Text type="secondary">Coming soon</Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <ContainerOutlined style={{ fontSize: 28, color: "#52c41a", marginBottom: 8 }} />
            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
              Packing Lists
            </Title>
            <Text type="secondary">Coming soon</Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <DollarOutlined style={{ fontSize: 28, color: "#fa8c16", marginBottom: 8 }} />
            <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>
              Commercial Invoices
            </Title>
            <Text type="secondary">Coming soon</Text>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
