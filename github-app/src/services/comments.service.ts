import { logger } from '../config/logger';

export interface ScanResult {
  scanId: string;
  violations: any[];
  enforcement: {
    blocking: any[];
    warning: any[];
    advisory: any[];
  };
  copilotAnalysis: any;
  filesAnalyzed: number;
  duration: number;
  repo: string;
  prNumber: number;
}

export class CommentsService {
  formatSummary(result: ScanResult): string {
    const { scanId, violations, enforcement, copilotAnalysis, filesAnalyzed, duration, repo, prNumber } = result;
    
    const criticalCount = enforcement.blocking.length;
    const highCount = enforcement.warning.length;
    const mediumCount = enforcement.advisory.length;
    
    let summary = `## 🛡️ Code Guardrails Security Report

**Scan ID:** \`${scanId}\` | **Duration:** ${duration.toFixed(2)}s | **Files Analyzed:** ${filesAnalyzed}

`;

    // Summary badges
    if (criticalCount > 0) {
      summary += `### 🚨 ${criticalCount} Critical Issue(s) - BLOCKING

`;
    } else {
      summary += `### ✅ No Critical Issues Found

`;
    }

    summary += `📊 **Summary:** ${violations.length} total issues (`;
    summary += `${criticalCount} critical, ${highCount} high, ${mediumCount} medium/low)

`;

    // Copilot detection
    if (copilotAnalysis.overallProbability > 0.5) {
      summary += `### 🤖 Copilot Detection

`;
      summary += `**Probability:** ${(copilotAnalysis.overallProbability * 100).toFixed(0)}% `;
      summary += `(**${copilotAnalysis.confidence}** confidence)

`;
      summary += `${copilotAnalysis.reasoning}

`;
      summary += `> ℹ️ AI-generated code receives extra security scrutiny.

`;
    }

    // Critical issues
    if (enforcement.blocking.length > 0) {
      summary += `### 🔴 Critical Issues (Must Fix)

`;
      enforcement.blocking.slice(0, 5).forEach((v: any, idx: number) => {
        summary += this.formatViolation(v, idx + 1);
      });
      
      if (enforcement.blocking.length > 5) {
        summary += `
... and ${enforcement.blocking.length - 5} more critical issues.

`;
      }
    }

    // High severity
    if (enforcement.warning.length > 0) {
      summary += `### 🟠 High Severity Issues (Review Required)

`;
      enforcement.warning.slice(0, 3).forEach((v: any) => {
        summary += `- **${v.type || v.rule_id}** in \`${v.filename}\` (Line ${v.line})
`;
      });
      
      if (enforcement.warning.length > 3) {
        summary += `
... and ${enforcement.warning.length - 3} more high severity issues.

`;
      }
    }

    // Override instructions
    if (criticalCount > 0) {
      summary += `
---

### 💡 Override Instructions

`;
      summary += `If these issues have been reviewed and approved, comment:
`;
      summary += `\`\`\`
/guardrails override [justification]
\`\`\`

`;
      summary += `Example: \`/guardrails override Security team approved - false positive\`

`;
    }

    summary += `
---

`;
    summary += `**Powered by:** Gemini AI + Static Analysis | [View Audit Logs](${process.env.BACKEND_URL}/audit/${scanId})`;

    return summary;
  }

  private formatViolation(violation: any, num: number): string {
    let text = `#### ${num}. ${violation.type || violation.rule_id}

`;
    text += `**File:** \`${violation.filename}\` **(Line ${violation.line})**
`;
    text += `**Severity:** ${this.getSeverityEmoji(violation.severity)} ${violation.severity.toUpperCase()}
`;
    
    if (violation.cwe) {
      text += `**CWE:** ${violation.cwe} | `;
    }
    if (violation.owasp) {
      text += `**OWASP:** ${violation.owasp}
`;
    }
    
    text += `
**Description:** ${violation.description || violation.message}

`;
    
    if (violation.explanation) {
      text += `**Why This Matters:**
${violation.explanation}

`;
    }
    
    if (violation.suggestedFix) {
      text += `**How to Fix:**
\`\`\`
${violation.suggestedFix}
\`\`\`

`;
    }
    
    text += `---

`;
    
    return text;
  }

  private getSeverityEmoji(severity: string): string {
    const emojiMap: Record<string, string> = {
      'critical': '🔴',
      'high': '🟠',
      'medium': '🟡',
      'low': '🔵'
    };
    return emojiMap[severity.toLowerCase()] || '⚪';
  }
}
