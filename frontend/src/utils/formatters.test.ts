import assert from "node:assert/strict";
import test from "node:test";

import { formatCurrency, formatDateTime } from "./formatters";

test("formatCurrency formats values using Brazilian Portuguese currency", () => {
  assert.equal(formatCurrency(42.5), "R$ 42,50");
});

test("formatDateTime formats values using the Fortaleza time zone", () => {
  assert.equal(formatDateTime("2026-05-21T18:30:00-03:00"), "21/05/2026, 18:30");
});
