/**
 * Converts any Axios/DRF API error into a human-readable string.
 *
 * DRF returns errors in several shapes:
 *   { detail: "message" }         — single message (permissions, workflow blocks)
 *   { field: ["msg1", "msg2"] }   — field-level validation errors
 *   { non_field_errors: ["msg"] } — cross-field validation errors
 *   "plain string"                — rare but possible
 */
export function extractApiError(
  err: unknown,
  fallback = "Something went wrong. Please try again."
): string {
  const data = (err as { response?: { data?: unknown } })?.response?.data;
  if (!data) return fallback;
  if (typeof data === "string") return data;
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
