import { Context } from 'probot';
import { GeminiService } from '../services/gemini.service';
import { CopilotDetector } from '../services/copilot-detector.service';
import { CommentsService } from '../services/comments.service';
import { BackendApiClient } from '../services/backend-api.client';
import { logger } from '../config/logger';
import { AuditLogger } from '../services/audit-logger.service';

const geminiService = new GeminiService(process.env.GEMINI_API_KEY || '');
const copilotDetector = new CopilotDetector();
const commentsService = new CommentsService();
const backendClient = new BackendApiClient(process.env.BACKEND_URL || 'http://localhost:8000');
const auditLogger = new AuditLogger();

export async function handlePullRequest(context: Context<'pull_request.opened' | 'pull_request.synchronize'>) {
  const startTime = Date.now();
  const pr = context.payload.pull_request;
  const repo = context.payload.repository;
  
  const scanId = `scan_${repo.owner.login}_${repo.name}_${pr.number}_${Date.now()}`;
  
  logger.info('Starting PR analysis', {
    scanId,
    pr: pr.number,
    repo: repo.full_name,
    files: pr.changed_files
  });

  try {
    // Create initial check run
    const checkRun = await context.octokit.checks.create({
      owner: repo.owner.login,
      repo: repo.name,
      name: 'Code Guardrails',
      head_sha: pr.head.sha,
      status: 'in_progress',
      started_at: new Date().toISOString(),
      output: {
        title: '🛡️ Analyzing code security...',
        summary: 'Running comprehensive security analysis'
      }
    });

    // Get PR files
    const { data: files } = await context.octokit.pulls.listFiles({
      owner: repo.owner.login,
      repo: repo.name,
      pull_number: pr.number,
      per_page: 100
    });

    logger.info('Retrieved PR files', { count: files.length, scanId });

    // Detect Copilot-generated code
    const copilotAnalysis = await copilotDetector.analyze(context, pr);
    
    logger.info('Copilot detection completed', {
      scanId,
      detected: copilotAnalysis.overallProbability > 0.5,
      probability: copilotAnalysis.overallProbability,
      confidence: copilotAnalysis.confidence
    });

    // Analyze files with backend
    const analysisPromises = files
      .filter(file => file.status !== 'removed' && file.patch)
      .map(async (file) => {
        try {
          // Get file content
          const content = await getFileContent(context, repo.owner.login, repo.name, file.filename, pr.head.sha);
          
          // Send to backend for analysis
          const backendResult = await backendClient.analyzeFile({
            code: content,
            filename: file.filename,
            language: detectLanguage(file.filename),
            copilot_detected: copilotAnalysis.overallProbability > 0.5
          });

          // Also run Gemini analysis
          const geminiResult = await geminiService.analyzeSecurityWithGemini(
            content,
            file.filename,
            detectLanguage(file.filename)
          );

          return {
            filename: file.filename,
            backendViolations: backendResult.violations || [],
            geminiViolations: geminiResult.vulnerabilities || [],
            additions: file.additions,
            deletions: file.deletions
          };
        } catch (error) {
          logger.error('File analysis failed', { error, filename: file.filename, scanId });
          return {
            filename: file.filename,
            backendViolations: [],
            geminiViolations: [],
            additions: file.additions,
            deletions: file.deletions,
            error: error.message
          };
        }
      });

    const analysisResults = await Promise.all(analysisPromises);

    // Merge and deduplicate violations
    const allViolations = mergeViolations(analysisResults);

    // Apply policy enforcement
    const policy = await backendClient.getPolicy(repo.owner.login, repo.name);
    const enforcement = applyPolicyEnforcement(allViolations, policy);

    const duration = (Date.now() - startTime) / 1000;

    logger.info('Analysis completed', {
      scanId,
      violations: allViolations.length,
      blocking: enforcement.blocking.length,
      duration
    });

    // Format and post comment
    const commentBody = commentsService.formatSummary({
      scanId,
      violations: allViolations,
      enforcement,
      copilotAnalysis,
      filesAnalyzed: files.length,
      duration,
      repo: repo.full_name,
      prNumber: pr.number
    });

    await context.octokit.issues.createComment({
      owner: repo.owner.login,
      repo: repo.name,
      issue_number: pr.number,
      body: commentBody
    });

    // Update check run
    const conclusion = enforcement.blocking.length > 0 ? 'failure' : 'success';
    const title = enforcement.blocking.length > 0 
      ? `❌ ${enforcement.blocking.length} blocking issue(s) found`
      : '✅ No blocking issues found';

    await context.octokit.checks.update({
      owner: repo.owner.login,
      repo: repo.name,
      check_run_id: checkRun.data.id,
      status: 'completed',
      conclusion,
      completed_at: new Date().toISOString(),
      output: {
        title,
        summary: `Found ${allViolations.length} total issues (${enforcement.blocking.length} blocking, ${enforcement.warning.length} warnings, ${enforcement.advisory.length} advisory)`,
        text: commentBody.substring(0, 65535) // GitHub limit
      }
    });

    // Log to audit
    await auditLogger.logScan({
      scanId,
      repository: repo.full_name,
      prNumber: pr.number,
      commitSha: pr.head.sha,
      violationsFound: allViolations.length,
      blockingCount: enforcement.blocking.length,
      copilotDetected: copilotAnalysis.overallProbability > 0.5,
      duration,
      status: 'completed'
    });

    logger.info('PR analysis completed successfully', { scanId, duration });

  } catch (error) {
    logger.error('PR analysis failed', { error, scanId, pr: pr.number });

    // Log failure to audit
    await auditLogger.logScan({
      scanId,
      repository: repo.full_name,
      prNumber: pr.number,
      commitSha: pr.head.sha,
      violationsFound: 0,
      blockingCount: 0,
      copilotDetected: false,
      duration: (Date.now() - startTime) / 1000,
      status: 'failed',
      error: error.message
    });

    // Post error comment
    await context.octokit.issues.createComment({
      owner: repo.owner.login,
      repo: repo.name,
      issue_number: pr.number,
      body: `## ⚠️ Analysis Failed

An error occurred during security analysis:
\`\`\`
${error.message}
\`\`\`

Please contact support or try again.`
    });
  }
}

async function getFileContent(
  context: Context<'pull_request.opened' | 'pull_request.synchronize'>,
  owner: string,
  repo: string,
  path: string,
  ref: string
): Promise<string> {
  try {
    const { data } = await context.octokit.repos.getContent({
      owner,
      repo,
      path,
      ref
    });

    if ('content' in data && data.content) {
      return Buffer.from(data.content, 'base64').toString('utf-8');
    }
    return '';
  } catch (error) {
    logger.error('Failed to get file content', { error, path });
    return '';
  }
}

function detectLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'jsx': 'javascript',
    'tsx': 'typescript',
    'java': 'java',
    'go': 'go',
    'rb': 'ruby',
    'php': 'php',
    'cs': 'csharp',
    'cpp': 'cpp',
    'c': 'c',
    'rs': 'rust'
  };
  return languageMap[ext || ''] || 'unknown';
}

function mergeViolations(results: any[]): any[] {
  const violations: any[] = [];
  
  for (const result of results) {
    // Add backend violations
    violations.push(...(result.backendViolations || []).map((v: any) => ({
      ...v,
      source: 'static',
      filename: result.filename
    })));

    // Add Gemini violations
    violations.push(...(result.geminiViolations || []).map((v: any) => ({
      ...v,
      source: 'ai',
      filename: result.filename
    })));
  }

  // Deduplicate based on file, line, and type
  const seen = new Set();
  return violations.filter(v => {
    const key = `${v.filename}:${v.line}:${v.type || v.rule_id}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function applyPolicyEnforcement(violations: any[], policy: any) {
  const blocking: any[] = [];
  const warning: any[] = [];
  const advisory: any[] = [];

  for (const violation of violations) {
    const severity = violation.severity || 'medium';
    
    if (policy.enforcement === 'blocking') {
      if (severity === 'critical' || severity === 'high') {
        blocking.push(violation);
      } else if (severity === 'medium') {
        warning.push(violation);
      } else {
        advisory.push(violation);
      }
    } else if (policy.enforcement === 'warning') {
      if (severity === 'critical' || severity === 'high') {
        warning.push(violation);
      } else {
        advisory.push(violation);
      }
    } else {
      advisory.push(violation);
    }
  }

  return { blocking, warning, advisory };
}
