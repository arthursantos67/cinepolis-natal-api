import assert from "node:assert/strict";
import test from "node:test";

import { resolveApiBaseUrl } from "./client";

test("resolveApiBaseUrl uses the configured backend base URL without trailing slashes", () => {
  assert.equal(
    resolveApiBaseUrl("http://api.local:8000///"),
    "http://api.local:8000"
  );
});

test("resolveApiBaseUrl falls back to the local backend URL", () => {
  assert.equal(resolveApiBaseUrl(""), "http://localhost:8000");
});
