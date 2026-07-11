#!/usr/bin/env node

import assert from "node:assert/strict";
import fs from "node:fs";

const workflowPath = ".github/workflows/issue-claim-guidance.yml";
const workflow = fs.readFileSync(workflowPath, "utf8");
const scriptMarker = "          script: |\n";
const markerIndex = workflow.indexOf(scriptMarker);
assert.notEqual(markerIndex, -1, "workflow must contain a github-script block");

const embeddedScript = workflow
  .slice(markerIndex + scriptMarker.length)
  .split("\n")
  .map((line) => (line.startsWith("            ") ? line.slice(12) : line))
  .join("\n");
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const runWorkflowScript = new AsyncFunction("github", "context", "core", embeddedScript);

function botComment(
  body,
  id = 1,
  { login = "github-actions[bot]", updatedAt = "2026-07-11T00:00:00Z" } = {},
) {
  return {
    id,
    user: { type: "Bot", login },
    body,
    created_at: updatedAt,
    updated_at: updatedAt,
  };
}

async function runScenario({
  login = "alice",
  body = "/renew",
  commentId = 9001,
  comments = [],
  labels = [{ name: "claimed" }],
  assignees = [],
  createdAt = "2026-07-11T00:00:00Z",
} = {}) {
  const calls = {
    paginate: 0,
    addLabels: [],
    addAssignees: [],
    removeLabel: [],
    updateComment: [],
    createComment: [],
  };
  const issues = {
    listComments: async () => ({ data: comments }),
    get: async () => ({ data: { labels, assignees } }),
    addLabels: async (args) => {
      calls.addLabels.push(args);
      return { data: {} };
    },
    addAssignees: async (args) => {
      calls.addAssignees.push(args);
      return { data: {} };
    },
    removeLabel: async (args) => {
      calls.removeLabel.push(args);
      return { data: {} };
    },
    updateComment: async (args) => {
      calls.updateComment.push(args);
      return { data: {} };
    },
    createComment: async (args) => {
      calls.createComment.push(args);
      return { data: {} };
    },
  };
  const github = {
    paginate: async (method, args) => {
      calls.paginate += 1;
      return (await method(args)).data;
    },
    rest: { issues },
  };
  const context = {
    payload: {
      issue: { number: 21 },
      comment: {
        id: commentId,
        body,
        created_at: createdAt,
        user: { login, type: "User" },
      },
    },
    repo: { owner: "duct-tape2", repo: "ai-language-partner" },
  };
  const core = { info() {}, warning() {} };

  await runWorkflowScript(github, context, core);
  return calls;
}

const interloper = await runScenario({
  login: "bob",
  comments: [botComment("<!-- ai-language-partner:issue-claim-guidance:bob -->")],
});
assert.equal(interloper.paginate, 1);
assert.equal(interloper.updateComment.length, 0);
assert.equal(interloper.createComment.length, 1);
assert.match(interloper.createComment[0].body, /not currently reserved for you/);

const claimant = await runScenario({
  login: "alice",
  comments: [
    botComment(
      [
        "<!-- ai-language-partner:issue-claim-guidance:alice -->",
        "<!-- ai-language-partner:claim-lease:alice:2026-07-12T00:00:00.000Z -->",
        "- Reservation check-in: old value",
      ].join("\n"),
    ),
  ],
});
assert.equal(claimant.createComment.length, 0);
assert.equal(claimant.updateComment.length, 1);
assert.match(claimant.updateComment[0].body, /2026-07-14T00:00:00.000Z/);
assert.equal(
  claimant.updateComment[0].body.match(/ai-language-partner:claim-lease:/g)?.length,
  1,
);

const staleClaimant = await runScenario({
  login: "alice",
  comments: [
    botComment(
      [
        "<!-- ai-language-partner:issue-claim-guidance:alice -->",
        "<!-- ai-language-partner:claim-lease:alice:2026-07-13T00:00:00.000Z -->",
      ].join("\n"),
      1,
      { updatedAt: "2026-07-11T01:00:00Z" },
    ),
    botComment(
      [
        "<!-- ai-language-partner:issue-claim-guidance:bob -->",
        "<!-- ai-language-partner:claim-lease:bob:2026-07-14T00:00:00.000Z -->",
      ].join("\n"),
      2,
      { updatedAt: "2026-07-11T00:30:00Z" },
    ),
  ],
});
assert.equal(staleClaimant.updateComment.length, 0);
assert.match(staleClaimant.createComment[0].body, /not currently reserved for you/);

const leaseA = [
  "<!-- ai-language-partner:issue-claim-guidance:alice -->",
  "<!-- ai-language-partner:claim-lease:alice:2026-07-13T00:00:00.000Z -->",
].join("\n");
const leaseB = [
  "<!-- ai-language-partner:issue-claim-guidance:bob -->",
  "<!-- ai-language-partner:claim-lease:bob:2026-07-14T00:00:00.000Z -->",
].join("\n");
const staleClaimBump = await runScenario({
  login: "alice",
  body: "/claim",
  commentId: 7001,
  comments: [botComment(leaseA, 1), botComment(leaseB, 2)],
});
assert.equal(staleClaimBump.updateComment.length, 1);
const staleAfterBump = await runScenario({
  login: "alice",
  commentId: 7002,
  comments: [
    botComment(staleClaimBump.updateComment[0].body, 1, {
      updatedAt: "2026-07-11T02:00:00Z",
    }),
    botComment(leaseB, 2, { updatedAt: "2026-07-11T00:30:00Z" }),
  ],
});
assert.equal(staleAfterBump.updateComment.length, 0);
assert.match(staleAfterBump.createComment[0].body, /not currently reserved for you/);

const expiredClaimant = await runScenario({
  login: "alice",
  comments: [
    botComment(
      [
        "<!-- ai-language-partner:issue-claim-guidance:alice -->",
        "<!-- ai-language-partner:claim-lease:alice:2026-07-10T23:59:59.000Z -->",
      ].join("\n"),
    ),
  ],
});
assert.equal(expiredClaimant.updateComment.length, 0);
assert.match(expiredClaimant.createComment[0].body, /not currently reserved for you/);

const untrustedBot = await runScenario({
  login: "alice",
  comments: [
    botComment(
      [
        "<!-- ai-language-partner:issue-claim-guidance:alice -->",
        "<!-- ai-language-partner:claim-lease:alice:2026-07-14T00:00:00.000Z -->",
      ].join("\n"),
      1,
      { login: "other-app[bot]" },
    ),
  ],
});
assert.equal(untrustedBot.updateComment.length, 0);
assert.match(untrustedBot.createComment[0].body, /not currently reserved for you/);

const assignedClaimant = await runScenario({
  login: "alice",
  assignees: [{ login: "alice" }],
});
assert.equal(assignedClaimant.updateComment.length, 0);
assert.equal(assignedClaimant.createComment.length, 1);
assert.match(assignedClaimant.createComment[0].body, /reservation for #21 is renewed/);

const secondClaim = await runScenario({
  login: "bob",
  body: "/claim",
});
assert.equal(secondClaim.createComment.length, 1);
assert.doesNotMatch(secondClaim.createComment[0].body, /claim-lease/);

const duplicateEvent = await runScenario({
  login: "alice",
  commentId: 4242,
  comments: [botComment("<!-- ai-language-partner:issue-claim-event:4242 -->")],
});
assert.equal(duplicateEvent.createComment.length, 0);
assert.equal(duplicateEvent.updateComment.length, 0);

const untrustedDuplicateEvent = await runScenario({
  login: "alice",
  body: "/claim",
  commentId: 5151,
  labels: [],
  comments: [
    botComment("<!-- ai-language-partner:issue-claim-event:5151 -->", 1, {
      login: "other-app[bot]",
    }),
  ],
});
assert.equal(untrustedDuplicateEvent.addLabels.length, 1);
assert.equal(untrustedDuplicateEvent.createComment.length, 1);

console.log("claim guidance behavior OK");
