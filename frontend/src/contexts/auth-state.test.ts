import assert from "node:assert/strict";
import test from "node:test";

import {
  applyAccessRefresh,
  applyCurrentUser,
  applyLogin,
  applyLogout,
  initialAuthState,
  isAuthenticated,
  startAuthLoading,
} from "./auth-state";

const user = {
  created_at: "2026-05-21T10:00:00Z",
  email: "orlando@gmail.com",
  id: "user-1",
  username: "pablo2265",
};

test("auth state starts without persisted tokens or user data", () => {
  assert.deepEqual(initialAuthState, {
    accessToken: null,
    refreshToken: null,
    status: "unauthenticated",
    user: null,
  });
  assert.equal(isAuthenticated(initialAuthState), false);
});

test("login stores access and refresh tokens in memory state", () => {
  const state = applyLogin(initialAuthState, {
    access: "access-token",
    refresh: "refresh-token",
  });

  assert.equal(state.accessToken, "access-token");
  assert.equal(state.refreshToken, "refresh-token");
  assert.equal(state.status, "loading");
  assert.equal(state.user, null);
  assert.equal(isAuthenticated(state), false);
});

test("current user completes authentication state", () => {
  const withTokens = applyLogin(initialAuthState, {
    access: "access-token",
    refresh: "refresh-token",
  });
  const state = applyCurrentUser(withTokens, user);

  assert.equal(state.status, "authenticated");
  assert.deepEqual(state.user, user);
  assert.equal(isAuthenticated(state), true);
});

test("refresh updates only the access token", () => {
  const authenticated = applyCurrentUser(
    applyLogin(initialAuthState, {
      access: "old-access",
      refresh: "refresh-token",
    }),
    user
  );
  const refreshed = applyAccessRefresh(authenticated, "new-access");

  assert.equal(refreshed.accessToken, "new-access");
  assert.equal(refreshed.refreshToken, "refresh-token");
  assert.deepEqual(refreshed.user, user);
});

test("logout clears tokens and protected identity state", () => {
  const authenticated = applyCurrentUser(
    applyLogin(initialAuthState, {
      access: "access-token",
      refresh: "refresh-token",
    }),
    user
  );

  assert.deepEqual(applyLogout(), initialAuthState);
  assert.notDeepEqual(authenticated, applyLogout());
});

test("loading status can be represented without exposing protected content", () => {
  assert.equal(startAuthLoading(initialAuthState).status, "loading");
});
