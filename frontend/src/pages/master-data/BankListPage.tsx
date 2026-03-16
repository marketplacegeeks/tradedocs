// Bank list page — shows all bank accounts in a table.
// Checker and Company Admin can create or edit banks.
// Makers can only view (they need the list to populate PI/CI dropdowns).

import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Button, Table, Space, Typography, Flex } from "antd";
import { PlusOutlined } from "@ant-design/icons";

import { listBanks } from "../../api/banks";
import type { Bank } from "../../api/banks";
import { useAuth } from "../../store/AuthContext";
import { ROLES, ACCOUNT_TYPE_LABELS } from "../../utils/constants";
import type { AccountType } from "../../utils/constants";

const { Title } = Typography;

export default function BankListPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Only Checker and Company Admin can write.
  const canWrite =
    user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;

  // Fetch all banks — cached by TanStack Query.
  // Constraint #25: query keys follow the pattern [resource].
  const { data: banks = [], isLoading } = useQuery({
    queryKey: ["banks"],
    queryFn: listBanks,
  });

  const columns = [
    {
      title: "Nickname",
      dataIndex: "nickname",
      key: "nickname",
      sorter: (a: Bank, b: Bank) => a.nickname.localeCompare(b.nickname),
    },
    {
      title: "Bank Name",
      dataIndex: "bank_name",
      key: "bank_name",
    },
    {
      title: "Beneficiary Name",
      dataIndex: "beneficiary_name",
      key: "beneficiary_name",
    },
    {
      title: "Account Number",
      dataIndex: "account_number",
      key: "account_number",
    },
    {
      title: "Account Type",
      dataIndex: "account_type",
      key: "account_type",
      render: (val: string) => ACCOUNT_TYPE_LABELS[val as AccountType] ?? val,
    },
    {
      title: "Currency",
      dataIndex: "currency_code",
      key: "currency_code",
    },
    {
      title: "Country",
      dataIndex: "bank_country_name",
      key: "bank_country_name",
    },
    {
      title: "SWIFT",
      dataIndex: "swift_code",
      key: "swift_code",
      render: (val: string) => val || "—",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: Bank) => (
        <Space>
          {canWrite && (
            <Button
              size="small"
              onClick={() => navigate(`/master-data/banks/${record.id}/edit`)}
            >
              Edit
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Bank Accounts
        </Title>
        {canWrite && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate("/master-data/banks/new")}
          >
            New Bank Account
          </Button>
        )}
      </Flex>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={banks}
        columns={columns}
        pagination={{ pageSize: 20 }}
      />
    </div>
  );
}
