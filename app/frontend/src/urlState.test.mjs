import test from "node:test";
import assert from "node:assert/strict";

import {
  buildReviewerShareUrl,
  buildReviewerUrlSearch,
  parseReviewerUrlState,
} from "./urlState.js";

test("parse shared state from search and hash", () => {
  assert.deepEqual(
    parseReviewerUrlState("?tab=governance&role=Admin", "#console"),
    {
      page: "console",
      tab: "governance",
      role: "Admin",
    }
  );
});

test("serialize shared state without default noise", () => {
  assert.equal(
    buildReviewerUrlSearch({ tab: "architecture", role: "Employee" }),
    ""
  );
  assert.equal(
    buildReviewerUrlSearch({ tab: "governance", role: "Admin" }),
    "tab=governance&role=Admin"
  );
});

test("build absolute share url", () => {
  assert.equal(
    buildReviewerShareUrl(
      { page: "console", tab: "ops", role: "Ops" },
      { origin: "https://atelier.example", pathname: "/" }
    ),
    "https://atelier.example/?tab=ops&role=Ops#console"
  );
});
