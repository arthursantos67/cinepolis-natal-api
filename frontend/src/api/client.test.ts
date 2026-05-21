import assert from "node:assert/strict";
import test from "node:test";

import {
  API_ERROR_MESSAGES,
  ApiError,
  apiRequest,
  buildApiUrl,
  getApiErrorUserMessage,
  isPaginatedResponse,
  resolveApiBaseUrl,
  type PaginatedResponse,
} from "./client";

test("resolveApiBaseUrl uses the configured backend base URL without trailing slashes", () => {
  assert.equal(
    resolveApiBaseUrl("http://api.local:8000///"),
    "http://api.local:8000"
  );
});

test("resolveApiBaseUrl falls back to the local backend URL", () => {
  assert.equal(resolveApiBaseUrl(""), "http://localhost:8000");
});

test("buildApiUrl joins relative paths with the normalized backend base URL", () => {
  assert.equal(
    buildApiUrl("api/v1/catalog/movies/", "http://api.local:8000/"),
    "http://api.local:8000/api/v1/catalog/movies/"
  );
});

test("apiRequest applies JSON headers, bearer token, and custom request options", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (input, init) => {
      assert.equal(input, "http://api.local:8000/api/v1/protected/");
      assert.equal(init?.method, "POST");
      assert.equal(init?.cache, "no-store");
      assert.equal(init?.body, JSON.stringify({ ok: true }));

      const headers = new Headers(init?.headers);
      assert.equal(headers.get("Accept"), "application/json");
      assert.equal(headers.get("Content-Type"), "application/json");
      assert.equal(headers.get("Authorization"), "Bearer access-token");

      return Response.json({ success: true });
    };

    const response = await apiRequest<{ success: boolean }>(
      "/api/v1/protected/",
      {
        baseUrl: "http://api.local:8000/",
        cache: "no-store",
        json: { ok: true },
        method: "POST",
        token: "access-token",
      }
    );

    assert.deepEqual(response, { success: true });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("apiRequest safely returns null for empty responses", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () => new Response(null, { status: 204 });

    const response = await apiRequest<null>("/api/v1/logout/", {
      baseUrl: "http://api.local:8000",
    });

    assert.equal(response, null);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("apiRequest throws ApiError with backend envelope metadata", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async () =>
      Response.json(
        {
          error: {
            code: "SEAT_ALREADY_RESERVED",
            details: { session_seat_id: 42 },
            message: "One or more selected seats are already reserved.",
            status: 409,
          },
        },
        {
          headers: { "X-Correlation-ID": "request-123" },
          status: 409,
        }
      );

    await assert.rejects(
      apiRequest("/api/v1/reservations/seats/", {
        baseUrl: "http://api.local:8000",
      }),
      (error) => {
        assert.ok(error instanceof ApiError);
        assert.equal(error.status, 409);
        assert.equal(error.code, "SEAT_ALREADY_RESERVED");
        assert.equal(error.message, "One or more selected seats are already reserved.");
        assert.deepEqual(error.details, { session_seat_id: 42 });
        assert.equal(error.correlationId, "request-123");
        return true;
      }
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("getApiErrorUserMessage maps known backend codes without exposing raw backend messages", () => {
  for (const [code, message] of Object.entries(API_ERROR_MESSAGES)) {
    const error = new ApiError("Raw backend message.", 400, {
      code,
      details: {},
    });

    assert.equal(getApiErrorUserMessage(error), message);
    assert.notEqual(getApiErrorUserMessage(error), error.message);
  }
});

test("getApiErrorUserMessage falls back safely for unknown backend codes", () => {
  const error = new ApiError("Raw backend detail.", 400, {
    code: "UNEXPECTED_BACKEND_CODE",
    details: {},
  });

  assert.equal(
    getApiErrorUserMessage(error),
    "Não foi possível concluir a solicitação. Tente novamente."
  );
});

test("isPaginatedResponse recognizes reusable DRF paginated response shape", () => {
  type MovieSummary = {
    id: number;
    title: string;
  };

  const response: unknown = {
    count: 1,
    next: null,
    previous: null,
    results: [{ id: 1, title: "Interestelar" }],
  };

  assert.equal(isPaginatedResponse<MovieSummary>(response), true);

  if (isPaginatedResponse<MovieSummary>(response)) {
    const paginated: PaginatedResponse<MovieSummary> = response;
    assert.equal(paginated.results[0]?.title, "Interestelar");
  }
});
