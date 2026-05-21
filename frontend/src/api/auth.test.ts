import assert from "node:assert/strict";
import test from "node:test";

import { authApi } from "./auth";

test("register posts visitor data to the canonical auth endpoint", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (input, init) => {
      assert.equal(input, "http://localhost:8000/api/v1/auth/register/");
      assert.equal(init?.method, "POST");
      assert.equal(
        init?.body,
        JSON.stringify({
          email: "ana@example.com",
          password: "senha-secreta",
          username: "ana",
        })
      );

      return Response.json(
        {
          created_at: "2026-05-21T10:00:00Z",
          email: "ana@example.com",
          id: "user-1",
          username: "ana",
        },
        { status: 201 }
      );
    };

    const response = await authApi.register({
      email: "ana@example.com",
      password: "senha-secreta",
      username: "ana",
    });

    assert.equal(response.email, "ana@example.com");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("login posts credentials and returns in-memory token data", async () => {
  const originalFetch = globalThis.fetch;

  try {
    globalThis.fetch = async (input, init) => {
      assert.equal(input, "http://localhost:8000/api/v1/auth/login/");
      assert.equal(init?.method, "POST");
      assert.equal(
        init?.body,
        JSON.stringify({
          email: "ana@example.com",
          password: "senha-secreta",
        })
      );

      return Response.json({
        access: "access-token",
        refresh: "refresh-token",
      });
    };

    const response = await authApi.login({
      email: "ana@example.com",
      password: "senha-secreta",
    });

    assert.deepEqual(response, {
      access: "access-token",
      refresh: "refresh-token",
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
