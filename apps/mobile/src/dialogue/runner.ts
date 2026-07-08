// F2. Dialogue runner — walks the shipped dialogue_bank_story_v1 node graph.
// (The backend does NOT ship ink; story.json is a scenario/node graph, so no inkjs.)
// The runner OWNS conversation state (current node); the server stays stateless.
import type { AdvanceResult, Candidate, DialogueStory, PersonaTurn, StoryNode, StoryScenario } from './types';

export type RunnerSnapshot = { scenarioId: string; nodeId: string | null };

function pickScenario(story: DialogueStory, filter?: { topicId?: string; level?: string; scenarioId?: string }): StoryScenario | null {
  if (!story.scenarios.length) return null;
  if (filter?.scenarioId) {
    const byId = story.scenarios.find((s) => s.scenarioId === filter.scenarioId);
    if (byId) return byId;
  }
  if (filter?.topicId || filter?.level) {
    const match = story.scenarios.find(
      (s) => (!filter.topicId || s.topicId === filter.topicId) && (!filter.level || s.level === filter.level),
    );
    if (match) return match;
    const byTopic = story.scenarios.find((s) => filter.topicId && s.topicId === filter.topicId);
    if (byTopic) return byTopic;
  }
  return story.scenarios[0];
}

export class DialogueRunner {
  private scenario: StoryScenario;
  private nodesById: Map<string, StoryNode>;
  private currentNodeId: string | null;

  constructor(story: DialogueStory, filter?: { topicId?: string; level?: string; scenarioId?: string }, snapshot?: RunnerSnapshot | null) {
    const scenario = (snapshot && story.scenarios.find((s) => s.scenarioId === snapshot.scenarioId)) || pickScenario(story, filter);
    this.scenario = scenario ?? { scenarioId: '', personaId: story.personaId, packVersion: story.packVersion, topicId: '', title: '', level: '', nodes: [] };
    this.nodesById = new Map(this.scenario.nodes.map((n) => [n.nodeId, n]));
    this.currentNodeId = snapshot ? snapshot.nodeId : (this.scenario.nodes[0]?.nodeId ?? null);
  }

  get scenarioId(): string {
    return this.scenario.scenarioId;
  }

  private resultForNode(nodeId: string | null): AdvanceResult {
    const node = nodeId ? this.nodesById.get(nodeId) : undefined;
    if (!node) return { persona: null, choices: [], ended: true, nodeId: null };
    const persona: PersonaTurn = { lineId: node.assistantLineId, text: node.assistantText, ko: node.assistantKo };
    const choices: Candidate[] = node.choices.map((c, i) => ({ index: i, lineId: c.lineId, text: c.text, ko: c.ko, nextNodeId: c.nextNodeId }));
    return { persona, choices, ended: choices.length === 0, nodeId: node.nodeId };
  }

  // The current node's persona line + candidate choices.
  current(): AdvanceResult {
    return this.resultForNode(this.currentNodeId);
  }

  // Advance to the chosen candidate's next node.
  choose(candidate: Candidate): AdvanceResult {
    this.currentNodeId = candidate.nextNodeId;
    return this.resultForNode(this.currentNodeId);
  }

  candidateLineIds(): string[] {
    const node = this.currentNodeId ? this.nodesById.get(this.currentNodeId) : undefined;
    return node ? node.choices.map((c) => c.lineId) : [];
  }

  snapshot(): RunnerSnapshot {
    return { scenarioId: this.scenario.scenarioId, nodeId: this.currentNodeId };
  }
}
