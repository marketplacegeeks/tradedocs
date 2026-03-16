// Organisation list page — shows all active organisations in a table.
// Checker and Company Admin can create new ones or deactivate existing ones.
// Makers can only view (they need the list to populate document dropdowns).

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Table, Tag, Space, Popconfirm, message, Typography, Flex } from "antd";
import { PlusOutlined } from "@ant-design/icons";

import { listOrganisations, updateOrganisation } from "../../api/organisations";
import type { Organisation } from "../../api/organisations";
import { useAuth } from "../../store/AuthContext";
import { ROLES, ORG_TAG_LABELS } from "../../utils/constants";
import type { OrgTag } from "../../utils/constants";

const { Title } = Typography;

// Tag colours for the document role badges.
const TAG_COLOURS: Record<string, string> = {
  EXPORTER: "blue",
  CONSIGNEE: "green",
  BUYER: "orange",
  NOTIFY_PARTY: "purple",
};

export default function OrganisationListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Only Checker and Company Admin can write.
  const canWrite =
    user?.role === ROLES.CHECKER || user?.role === ROLES.COMPANY_ADMIN;

  // Fetch organisations — cached by TanStack Query with key ["organisations"].
  // Constraint #25: query keys follow the pattern [resource].
  const { data: organisations = [], isLoading } = useQuery({
    queryKey: ["organisations"],
    queryFn: () => listOrganisations(),
  });

  // Deactivate mutation — sends PATCH { is_active: false }.
  const deactivateMutation = useMutation({
    mutationFn: (id: number) => updateOrganisation(id, { is_active: false }),
    onSuccess: () => {
      message.success("Organisation deactivated.");
      // Refetch the list so the deactivated org disappears immediately.
      queryClient.invalidateQueries({ queryKey: ["organisations"] });
    },
    onError: () => {
      message.error("Failed to deactivate organisation.");
    },
  });

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      sorter: (a: Organisation, b: Organisation) => a.name.localeCompare(b.name),
    },
    {
      title: "IEC Code",
      dataIndex: "iec_code",
      key: "iec_code",
      render: (val: string | null) => val ?? "—",
    },
    {
      title: "Roles",
      key: "tags",
      render: (_: unknown, record: Organisation) =>
        record.tags.map((t) => (
          <Tag key={t.tag} color={TAG_COLOURS[t.tag] ?? "default"}>
            {ORG_TAG_LABELS[t.tag as OrgTag] ?? t.tag}
          </Tag>
        )),
    },
    {
      title: "Addresses",
      key: "addresses",
      render: (_: unknown, record: Organisation) => record.addresses.length,
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: Organisation) => (
        <Space>
          <Button size="small" onClick={() => navigate(`/master-data/organisations/${record.id}/edit`)}>
            Edit
          </Button>
          {canWrite && (
            <Popconfirm
              title="Deactivate this organisation?"
              description="It will no longer appear in document dropdowns."
              onConfirm={() => deactivateMutation.mutate(record.id)}
              okText="Deactivate"
              cancelText="Cancel"
            >
              <Button size="small" danger>
                Deactivate
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Organisations
        </Title>
        {canWrite && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate("/master-data/organisations/new")}
          >
            New Organisation
          </Button>
        )}
      </Flex>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={organisations}
        columns={columns}
        pagination={{ pageSize: 20 }}
      />
    </div>
  );
}
