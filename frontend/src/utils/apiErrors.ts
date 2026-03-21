/**
 * Converts any Axios/DRF API error into a human-readable string safe for
 * business users. Handles four cases:
 *
 *   500-level errors  — server crash; return a generic "contact admin" message
 *   HTML response     — Django debug page leaked; hide it, return fallback
 *   { detail: "…" }  — single message (permissions, workflow blocks)
 *   { field: […] }   — field-level validation errors from DRF
 */
export function extractApiError(
  err: unknown,
  fallback = "Something went wrong. Please try again."
): string {
  const response = (err as { response?: { status?: number; data?: unknown } })
    ?.response;

  // 500-level server errors: never show raw crash details to business users.
  if (response?.status && response.status >= 500) {
    return "An unexpected server error occurred. Please try again, or contact your administrator if the problem persists.";
  }

  const data = response?.data;
  if (!data) return fallback;

  // Raw HTML (e.g. Django debug page): hide it entirely.
  if (typeof data === "string") {
    if (data.trimStart().startsWith("<")) return fallback;
    return data;
  }

  if (typeof data !== "object" || data === null) return fallback;

  const obj = data as Record<string, unknown>;

  // Single detail message — used for permission denials, workflow blocks, etc.
  if (typeof obj.detail === "string") return obj.detail;

  // Field-level errors: collect all fields into readable lines.
  const lines: string[] = [];
  for (const [field, messages] of Object.entries(obj)) {
    const text = Array.isArray(messages)
      ? messages.join(", ")
      : typeof messages === "string"
      ? messages
      : JSON.stringify(messages);
    // non_field_errors shown without a field prefix so they read naturally.
    lines.push(field === "non_field_errors" ? text : `${field}: ${text}`);
  }

  return lines.length > 0 ? lines.join("\n") : fallback;
}
