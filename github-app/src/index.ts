import { Probot } from 'probot';
import { handlePullRequest } from './handlers/pull-request.handler';
import { handleIssueComment } from './handlers/issue-comment.handler';

export = (app: Probot) => {
  console.log('🤖 GitHub Guardrails starting...');
  
  app.on('pull_request.opened', handlePullRequest);
  app.on('pull_request.synchronize', handlePullRequest);
  app.on('issue_comment.created', handleIssueComment);
  
  console.log('✅ GitHub Guardrails ready');
};
