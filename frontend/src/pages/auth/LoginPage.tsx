// Pre-login landing page (FR-02).
// Left column: product feature carousel.
// Right column: email + password login form.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Button, Card, Carousel, Col, Form, Input, Row, Tooltip, Typography, message,
} from "antd";
import { QuestionCircleOutlined } from "@ant-design/icons";

import { loginUser } from "../../api/auth";
import { useAuth } from "../../store/AuthContext";
import type { AuthUser } from "../../api/auth";

const { Title, Text, Paragraph } = Typography;

// ---- Zod schema -----------------------------------------------------------

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// ---- Feature slide content ------------------------------------------------

const SLIDES = [
  {
    title: "Create Proforma Invoices",
    description:
      "Generate professional Proforma Invoices in seconds. Add line items, apply charges, and send for approval — all in one place.",
  },
  {
    title: "Manage Packing Lists",
    description:
      "Track containers, items, and weights with precision. Build Packing Lists directly from your approved Proforma Invoice.",
  },
  {
    title: "Issue Commercial Invoices",
    description:
      "Produce print-ready Commercial Invoices with a guided 5-step wizard. Approved documents are locked and PDF-ready instantly.",
  },
];

// ---- Component ------------------------------------------------------------

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginFormValues) {
    setLoading(true);
    try {
      const { user, accessToken, refreshToken } = await loginUser(
        values.email,
        values.password
      );
      login(user as AuthUser, accessToken, refreshToken);
      navigate("/dashboard");
    } catch {
      message.error("Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Row style={{ minHeight: "100vh" }}>
      {/* Left column — feature carousel */}
      <Col
        xs={0}
        md={13}
        style={{
          background: "linear-gradient(135deg, #1677ff 0%, #0a3d91 100%)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "48px 64px",
        }}
      >
        <Title level={2} style={{ color: "#fff", marginBottom: 8 }}>
          TradeDocs
        </Title>
        <Text style={{ color: "rgba(255,255,255,0.75)", marginBottom: 48, fontSize: 16 }}>
          Trade documentation for export teams
        </Text>

        <Carousel autoplay dots={{ className: "carousel-dots" }}>
          {SLIDES.map((slide) => (
            <div key={slide.title}>
              <Title level={3} style={{ color: "#fff", marginBottom: 12 }}>
                {slide.title}
              </Title>
              <Paragraph style={{ color: "rgba(255,255,255,0.85)", fontSize: 15, maxWidth: 440 }}>
                {slide.description}
              </Paragraph>
            </div>
          ))}
        </Carousel>
      </Col>

      {/* Right column — login form */}
      <Col
        xs={24}
        md={11}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f5f5f5",
          padding: 24,
        }}
      >
        <Card style={{ width: "100%", maxWidth: 400 }} variant="borderless">
          <Title level={3} style={{ marginBottom: 4 }}>
            Sign in
          </Title>
          <Text type="secondary" style={{ display: "block", marginBottom: 32 }}>
            Enter your credentials to continue
          </Text>

          <Form layout="vertical" onFinish={handleSubmit(onSubmit)}>
            <Form.Item
              label="Email"
              required
              validateStatus={errors.email ? "error" : ""}
              help={errors.email?.message}
            >
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <Input
                    {...field}
                    type="email"
                    placeholder="you@example.com"
                    size="large"
                    autoComplete="email"
                    autoFocus
                  />
                )}
              />
            </Form.Item>

            <Form.Item
              label="Password"
              required
              validateStatus={errors.password ? "error" : ""}
              help={errors.password?.message}
            >
              <Controller
                name="password"
                control={control}
                render={({ field }) => (
                  <Input.Password
                    {...field}
                    placeholder="••••••••"
                    size="large"
                    autoComplete="current-password"
                  />
                )}
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 8 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                size="large"
                block
              >
                Log in
              </Button>
            </Form.Item>

            {/* Forgot password — no separate page; admin resets passwords manually */}
            <div style={{ textAlign: "right" }}>
              <Tooltip title="Contact your Company Admin to reset your password.">
                <Text
                  type="secondary"
                  style={{ cursor: "default", fontSize: 13 }}
                >
                  Forgot password? <QuestionCircleOutlined />
                </Text>
              </Tooltip>
            </div>
          </Form>
        </Card>
      </Col>
    </Row>
  );
}
