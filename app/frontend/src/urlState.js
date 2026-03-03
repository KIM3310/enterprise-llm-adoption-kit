const VALID_PAGES = new Set(["home", "capabilities", "validation", "scenario", "console"]);
const VALID_TABS = new Set(["architecture", "ops", "governance", "integrations"]);
const VALID_ROLES = new Set(["Employee", "Ops", "Admin"]);

function normalizeSearch(search) {
  return search.startsWith("?") ? search.slice(1) : search;
}

export function parseReviewerUrlState(search, hash = "") {
  const params = new URLSearchParams(normalizeSearch(search));
  const next = {};
  const page = String(hash || "").replace("#", "").trim().toLowerCase();
  const tab = params.get("tab");
  const role = params.get("role");

  if (VALID_PAGES.has(page)) {
    next.page = page;
  }
  if (tab && VALID_TABS.has(tab)) {
    next.tab = tab;
  }
  if (role && VALID_ROLES.has(role)) {
    next.role = role;
  }

  return next;
}

export function buildReviewerUrlSearch(state) {
  const params = new URLSearchParams();
  if (state.tab && state.tab !== "architecture") params.set("tab", state.tab);
  if (state.role && state.role !== "Employee") params.set("role", state.role);
  return params.toString();
}

export function replaceReviewerUrlState({ page, tab, role }) {
  if (typeof window === "undefined") return;
  const search = buildReviewerUrlSearch({ tab, role });
  const nextUrl = `${window.location.pathname}${search ? `?${search}` : ""}#${page || "home"}`;
  window.history.replaceState(window.history.state, "", nextUrl);
}

export function buildReviewerShareUrl(
  { page, tab, role },
  options = {}
) {
  const origin =
    options.origin ??
    (typeof window !== "undefined" ? window.location.origin : "");
  const pathname =
    options.pathname ??
    (typeof window !== "undefined" ? window.location.pathname : "/");
  const search = buildReviewerUrlSearch({ tab, role });
  return `${origin}${pathname}${search ? `?${search}` : ""}#${page || "home"}`;
}
