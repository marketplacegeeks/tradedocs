// Training page — embedded YouTube walkthroughs for TradeDocs.
// Visible to all roles.

const VIDEOS = [
  {
    id: "K8TPNLrJMJs",
    title: "User Management",
    description:
      "Learn how to create a combined Packing List and Commercial Invoice from an approved PI, and manage the joint approval workflow.",
    chip: "Beginner",
    chipColor: { bg: "var(--pastel-green)", text: "var(--pastel-green-text)" },
  },
  {
    id: "pXGLEN-F794",
    title: "Master Data",
    description:
      "A complete walkthrough of the platform — from creating your first Proforma Invoice to submitting it for approval.",
    chip: "Intermediate",
    chipColor: { bg: "var(--pastel-blue)", text: "var(--pastel-blue-text)" },
  },
];

export default function TrainingPage() {
  return (
    <div
      style={{
        padding: 32,
        background: "var(--bg-base)",
        minHeight: "100vh",
        fontFamily: "var(--font-body)",
      }}
    >
      {/* Page header */}
      <div style={{ marginBottom: 32 }}>
        <h1
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: 22,
            fontWeight: 700,
            color: "var(--text-primary)",
            margin: 0,
          }}
        >
          Training
        </h1>
        <p
          style={{
            fontSize: 14,
            color: "var(--text-secondary)",
            marginTop: 6,
            marginBottom: 0,
          }}
        >
          Learn how to use TradeDocs with these guided video walkthroughs.
        </p>
      </div>

      {/* Video grid — 2 columns on desktop, 1 on mobile */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))",
          gap: 24,
        }}
      >
        {VIDEOS.map((video, i) => (
          <div
            key={video.id}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-light)",
              borderRadius: 14,
              boxShadow: "var(--shadow-card)",
              overflow: "hidden",
              animation: `fadeUp 0.35s ease both`,
              animationDelay: `${i * 0.1}s`,
              transition: "box-shadow 0.15s ease, transform 0.15s ease",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.boxShadow =
                "0 4px 20px rgba(0,0,0,0.08)";
              (e.currentTarget as HTMLDivElement).style.transform =
                "translateY(-2px)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.boxShadow =
                "var(--shadow-card)";
              (e.currentTarget as HTMLDivElement).style.transform =
                "translateY(0)";
            }}
          >
            {/* 16:9 YouTube embed */}
            <div style={{ position: "relative", paddingTop: "56.25%" }}>
              <iframe
                src={`https://www.youtube.com/embed/${video.id}`}
                title={video.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                style={{
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                  border: "none",
                }}
              />
            </div>

            {/* Card body */}
            <div style={{ padding: "20px 24px" }}>
              {/* Difficulty chip */}
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "3px 10px",
                  borderRadius: 100,
                  fontSize: 11,
                  fontWeight: 600,
                  letterSpacing: "0.02em",
                  background: video.chipColor.bg,
                  color: video.chipColor.text,
                  marginBottom: 10,
                }}
              >
                {video.chip}
              </span>

              <h2
                style={{
                  fontFamily: "var(--font-heading)",
                  fontSize: 15,
                  fontWeight: 600,
                  color: "var(--text-primary)",
                  margin: "0 0 8px 0",
                }}
              >
                {video.title}
              </h2>

              <p
                style={{
                  fontSize: 13,
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                  margin: "0 0 16px 0",
                }}
              >
                {video.description}
              </p>

              <a
                href={`https://www.youtube.com/watch?v=${video.id}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  fontSize: 13,
                  fontWeight: 500,
                  color: "var(--primary)",
                  textDecoration: "none",
                }}
                onMouseEnter={(e) =>
                  ((e.currentTarget as HTMLAnchorElement).style.color =
                    "var(--primary-hover)")
                }
                onMouseLeave={(e) =>
                  ((e.currentTarget as HTMLAnchorElement).style.color =
                    "var(--primary)")
                }
              >
                Watch on YouTube →
              </a>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
