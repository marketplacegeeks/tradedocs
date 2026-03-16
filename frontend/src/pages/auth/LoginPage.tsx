// Pre-login landing page (FR-02).
// Left: animated feature carousel on a soft gradient.
// Right: clean login card on --bg-base.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { FileText, Package, DollarSign, ArrowRight, Building2 } from "lucide-react";

import { loginUser } from "../../api/auth";
import { useAuth } from "../../store/AuthContext";
import type { AuthUser } from "../../api/auth";

// ---- Schema ---------------------------------------------------------------

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});
type LoginFormValues = z.infer<typeof loginSchema>;

// ---- Feature slides -------------------------------------------------------

const SLIDES = [
  {
    icon: FileText,
    title: "Create Proforma Invoices",
    description:
      "Generate professional Proforma Invoices in seconds. Add line items, apply charges, and send for approval — all in one place.",
    chip: "Step 1",
    chipColor: "chip-blue",
  },
  {
    icon: Package,
    title: "Manage Packing Lists",
    description:
      "Track containers, items, and weights with precision. Build Packing Lists directly from your Approved Proforma Invoice.",
    chip: "Step 2",
    chipColor: "chip-green",
  },
  {
    icon: DollarSign,
    title: "Issue Commercial Invoices",
    description:
      "Produce print-ready Commercial Invoices with a guided 5-step wizard. Approved documents are locked and PDF-ready instantly.",
    chip: "Step 3",
    chipColor: "chip-purple",
  },
];

// ---- Component ------------------------------------------------------------

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [activeSlide, setActiveSlide] = useState(0);

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
    setErrorMsg("");
    try {
      const { user, accessToken, refreshToken } = await loginUser(values.email, values.password);
      login(user as AuthUser, accessToken, refreshToken);
      navigate("/dashboard");
    } catch {
      setErrorMsg("Invalid email or password. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const ActiveIcon = SLIDES[activeSlide].icon;

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "var(--bg-base)",
        fontFamily: "var(--font-body)",
      }}
    >
      {/* Left — feature panel */}
      <div
        style={{
          flex: "0 0 52%",
          background: "linear-gradient(145deg, #EEF1FF 0%, #E8EDFF 40%, #DDE8FF 100%)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "48px 64px",
          position: "relative",
          overflow: "hidden",
        }}
        className="login-left"
      >
        {/* Decorative background circle */}
        <div
          style={{
            position: "absolute",
            top: -80,
            right: -80,
            width: 320,
            height: 320,
            borderRadius: "50%",
            background: "rgba(79,110,247,0.08)",
            pointerEvents: "none",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: -60,
            left: -60,
            width: 240,
            height: 240,
            borderRadius: "50%",
            background: "rgba(79,110,247,0.05)",
            pointerEvents: "none",
          }}
        />

        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 56 }}>
          <Building2 size={26} strokeWidth={2} color="var(--primary)" />
          <span
            style={{
              fontFamily: "var(--font-heading)",
              fontWeight: 700,
              fontSize: 20,
              color: "var(--text-primary)",
            }}
          >
            TradeDocs
          </span>
        </div>

        {/* Active slide */}
        <div
          key={activeSlide}
          style={{ animation: "fadeUp 0.35s ease both", maxWidth: 420 }}
        >
          {/* Icon in pastel square */}
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: "var(--bg-surface)",
              boxShadow: "var(--shadow-card)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 20,
            }}
          >
            <ActiveIcon size={24} strokeWidth={1.5} color="var(--primary)" />
          </div>

          <span className={`chip ${SLIDES[activeSlide].chipColor}`} style={{ marginBottom: 14, display: "inline-flex" }}>
            {SLIDES[activeSlide].chip}
          </span>

          <h2
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 26,
              fontWeight: 700,
              color: "var(--text-primary)",
              margin: "12px 0 14px",
              lineHeight: 1.3,
            }}
          >
            {SLIDES[activeSlide].title}
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 15,
              color: "var(--text-secondary)",
              lineHeight: 1.65,
              marginBottom: 36,
            }}
          >
            {SLIDES[activeSlide].description}
          </p>
        </div>

        {/* Slide dots */}
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {SLIDES.map((_, i) => (
            <button
              key={i}
              onClick={() => setActiveSlide(i)}
              style={{
                width: i === activeSlide ? 24 : 8,
                height: 8,
                borderRadius: 100,
                border: "none",
                cursor: "pointer",
                background: i === activeSlide ? "var(--primary)" : "var(--border-medium)",
                transition: "all 0.2s ease",
                padding: 0,
              }}
            />
          ))}
          <button
            onClick={() => setActiveSlide((prev) => (prev + 1) % SLIDES.length)}
            style={{
              marginLeft: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
              borderRadius: "50%",
              border: "1px solid var(--border-medium)",
              cursor: "pointer",
              background: "var(--bg-surface)",
              color: "var(--text-muted)",
            }}
          >
            <ArrowRight size={14} strokeWidth={2} />
          </button>
        </div>
      </div>

      {/* Right — login form */}
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
        }}
      >
        <div style={{ width: "100%", maxWidth: 380 }}>
          <h1
            style={{
              fontFamily: "var(--font-heading)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 6,
            }}
          >
            Sign in
          </h1>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 14,
              color: "var(--text-muted)",
              marginBottom: 32,
            }}
          >
            Enter your credentials to continue
          </p>

          <form onSubmit={handleSubmit(onSubmit)}>
            {/* Email */}
            <div style={{ marginBottom: 16 }}>
              <label
                style={{
                  display: "block",
                  fontFamily: "var(--font-body)",
                  fontSize: 13,
                  fontWeight: 500,
                  color: "var(--text-primary)",
                  marginBottom: 6,
                }}
              >
                Email
              </label>
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <input
                    {...field}
                    type="email"
                    autoComplete="email"
                    autoFocus
                    placeholder="you@example.com"
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      background: "var(--bg-input)",
                      border: `1px solid ${errors.email ? "#F5222D" : "var(--border-medium)"}`,
                      borderRadius: 8,
                      fontFamily: "var(--font-body)",
                      fontSize: 14,
                      color: "var(--text-primary)",
                      outline: "none",
                    }}
                    onFocus={(e) => {
                      if (!errors.email) e.currentTarget.style.borderColor = "var(--primary)";
                    }}
                    onBlur={(e) => {
                      if (!errors.email) e.currentTarget.style.borderColor = "var(--border-medium)";
                    }}
                  />
                )}
              />
              {errors.email && (
                <p style={{ color: "#F5222D", fontSize: 12, marginTop: 4, fontFamily: "var(--font-body)" }}>
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <label
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 13,
                    fontWeight: 500,
                    color: "var(--text-primary)",
                  }}
                >
                  Password
                </label>
                <span
                  title="Contact your Company Admin to reset your password."
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 12,
                    color: "var(--text-muted)",
                    cursor: "default",
                  }}
                >
                  Forgot password?
                </span>
              </div>
              <Controller
                name="password"
                control={control}
                render={({ field }) => (
                  <input
                    {...field}
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    style={{
                      width: "100%",
                      padding: "10px 14px",
                      background: "var(--bg-input)",
                      border: `1px solid ${errors.password ? "#F5222D" : "var(--border-medium)"}`,
                      borderRadius: 8,
                      fontFamily: "var(--font-body)",
                      fontSize: 14,
                      color: "var(--text-primary)",
                      outline: "none",
                    }}
                    onFocus={(e) => {
                      if (!errors.password) e.currentTarget.style.borderColor = "var(--primary)";
                    }}
                    onBlur={(e) => {
                      if (!errors.password) e.currentTarget.style.borderColor = "var(--border-medium)";
                    }}
                  />
                )}
              />
              {errors.password && (
                <p style={{ color: "#F5222D", fontSize: 12, marginTop: 4, fontFamily: "var(--font-body)" }}>
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Error message */}
            {errorMsg && (
              <div
                style={{
                  background: "var(--pastel-pink)",
                  color: "var(--pastel-pink-text)",
                  borderRadius: 8,
                  padding: "10px 14px",
                  fontFamily: "var(--font-body)",
                  fontSize: 13,
                  marginBottom: 16,
                }}
              >
                {errorMsg}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "11px 18px",
                background: loading ? "var(--border-medium)" : "var(--primary)",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                fontFamily: "var(--font-body)",
                fontSize: 14,
                fontWeight: 500,
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
