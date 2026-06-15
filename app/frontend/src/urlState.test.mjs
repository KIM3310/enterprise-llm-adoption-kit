import test from "node:test";
import assert from "node:assert/strict";

import {
  buildArchitectureShareUrl,
  buildArchitectureUrlSearch,
  parseArchitectureUrlState,
} from "./urlState.js";

test("parse shared state from search and hash", () => {
  assert.deepEqual(
    parseArchitectureUrlState("?tab=governance&role=Admin", "#console"),
    {
      page: "console",
      tab: "governance",
      role: "Admin",
    }
  );
});

test("serialize shared state without default noise", () => {
  assert.equal(
    buildArchitectureUrlSearch({ tab: "architecture", role: "Employee" }),
    ""
  );
  assert.equal(
    buildArchitectureUrlSearch({ tab: "governance", role: "Admin" }),
    "tab=governance&role=Admin"
  );
});

test("build absolute share url", () => {
  assert.equal(
    buildArchitectureShareUrl(
      { page: "console", tab: "ops", role: "Ops" },
      { origin: "https://atelier.example", pathname: "/" }
    ),
    "https://atelier.example/?tab=ops&role=Ops#console"
  );
});
