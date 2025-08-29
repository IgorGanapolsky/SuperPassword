import { Octokit } from "@octokit/rest";

interface StatusUpdate {
  build: {
    status: string;
    url: string;
  };
  security: {
    alerts: number;
    critical: number;
  };
  coverage: {
    percentage: number;
    change: number;
  };
  prs: {
    total: number;
    ready: number;
    draft: number;
    needsReview: number;
  };
  activity: Array<{
    type: string;
    description: string;
    timestamp: string;
  }>;
}

export class StatusBoardController {
  private octokit: Octokit;
  private owner: string;
  private repo: string;
  private boardNumber: number | null = null;

  constructor(token: string, owner: string, repo: string) {
    this.octokit = new Octokit({ auth: token });
    this.owner = owner;
    this.repo = repo;
  }

  async initialize(): Promise<void> {
    const board = await this.findBoard();
    if (board) {
      this.boardNumber = board.number;
    } else {
      await this.createBoard();
    }
  }

  async update(status: StatusUpdate): Promise<void> {
    if (!this.boardNumber) {
      await this.initialize();
    }

    const comment = await this.formatStatus(status);
    await this.postUpdate(comment);
  }

  private async findBoard() {
    const { data: issues } = await this.octokit.issues.listForRepo({
      owner: this.owner,
      repo: this.repo,
      labels: ["status-board"],
      state: "open",
    });
    return issues[0];
  }

  private async createBoard() {
    const { data: issue } = await this.octokit.issues.create({
      owner: this.owner,
      repo: this.repo,
      title: "📊 SuperPassword Status Board",
      body: "Initializing status board...",
      labels: ["status-board"],
    });
    this.boardNumber = issue.number;
  }

  private formatStatus(status: StatusUpdate): string {
    const timestamp = new Date().toISOString();
    const buildEmoji = status.build.status === "success" ? "✅" : status.build.status === "failure" ? "❌" : "⏳";
    const securityEmoji = status.security.critical > 0 ? "🚨" : status.security.alerts > 0 ? "⚠️" : "✅";
    const coverageEmoji = status.coverage.percentage >= 80 ? "✅" : status.coverage.percentage >= 60 ? "⚠️" : "❌";

    return `## 📊 Status Board Update

### 🏗️ Build Status
${buildEmoji} Status: ${status.build.status}
🔗 [View Details](${status.build.url})

### 🛡️ Security
${securityEmoji} Alerts: ${status.security.alerts} (${status.security.critical} critical)

### 📊 Coverage
${coverageEmoji} Coverage: ${status.coverage.percentage}%
📈 Change: ${status.coverage.change > 0 ? "+" : ""}${status.coverage.change}%

### 👥 Pull Requests
- 📬 Total: ${status.prs.total}
- ✅ Ready to Merge: ${status.prs.ready}
- 📝 Draft: ${status.prs.draft}
- 👀 Needs Review: ${status.prs.needsReview}

### 📋 Recent Activity
${status.activity
  .map(
    (item) =>
      `- ${item.type === "build" ? "🏗️" : item.type === "pr" ? "🔄" : "📝"} ${
        item.description
      } (${item.timestamp})`
  )
  .join("
")}

_Last Updated: ${timestamp}_
_Next Update: In 5 minutes_`;
  }

  private async postUpdate(body: string): Promise<void> {
    if (!this.boardNumber) {
      throw new Error("Board not initialized");
    }

    await this.octokit.issues.createComment({
      owner: this.owner,
      repo: this.repo,
      issue_number: this.boardNumber,
      body,
    });
  }
}
