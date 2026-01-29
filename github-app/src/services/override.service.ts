import { Context } from 'probot';
import { logger } from '../config/logger';

export class OverrideService {
  async handleOverrideRequest(context: any, issue: any, comment: any) {
    const repo = context.payload.repository;
    const commentBody = comment.body.trim();
    
    // Extract reason
    const reason = commentBody.replace('/guardrails override', '').trim() || 'No reason provided';
    
    logger.info('Processing override request', {
      pr: issue.number,
      user: comment.user.login,
      reason
    });

    // Post approval request
    const approvalComment = await context.octokit.issues.createComment({
      owner: repo.owner.login,
      repo: repo.name,
      issue_number: issue.number,
      body: this.formatApprovalRequest(comment.user.login, reason)
    });

    // In a real implementation, you would:
    // 1. Set up webhook listener for reactions
    // 2. Watch for 👍 from authorized users
    // 3. Re-run check with override applied
    // 4. Log to audit database
    
    logger.info('Override request posted', {
      pr: issue.number,
      commentId: approvalComment.data.id
    });
  }

  private formatApprovalRequest(user: string, reason: string): string {
    return \`## 🔓 Override Request

**Requested by:** @\${user}  
**Reason:** \${reason}

**Security Team:** React with 👍 to approve this override, or comment \`/approve\` to bypass blocking issues.

> ⚠️ **Note:** Approving an override will allow the PR to merge despite security violations. Ensure proper review has been completed.

### Next Steps
1. Review the violations above
2. Verify the justification is valid
3. React with 👍 or comment \`/approve\` to approve
4. The check will be re-run with override applied
\`;
  }
}
