import { Context } from 'probot';

export async function handleIssueComment(context: Context<'issue_comment.created'>) {
  const comment = context.payload.comment.body;
  
  if (comment.includes('/guardrails override')) {
    await context.octokit.reactions.createForIssueComment({
      owner: context.payload.repository.owner.login,
      repo: context.payload.repository.name,
      comment_id: context.payload.comment.id,
      content: 'eyes'
    });
    
    await context.octokit.issues.createComment({
      owner: context.payload.repository.owner.login,
      repo: context.payload.repository.name,
      issue_number: context.payload.issue.number,
      body: '👍 Override requested. Awaiting approval from maintainer.'
    });
  }
}
