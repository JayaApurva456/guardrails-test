import axios, { AxiosInstance } from 'axios';
import { logger } from '../config/logger';

export interface AnalyzeFileRequest {
  code: string;
  filename: string;
  language: string;
  copilot_detected: boolean;
}

export interface Policy {
  enforcement: 'advisory' | 'warning' | 'blocking';
  rules: any[];
}

export class BackendApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async analyzeFile(request: AnalyzeFileRequest): Promise<any> {
    try {
      const { data } = await this.client.post('/api/analyze/file', request);
      return data;
    } catch (error) {
      logger.error('Backend API analyzeFile failed', { error, filename: request.filename });
      return { violations: [] };
    }
  }

  async getPolicy(owner: string, repo: string): Promise<Policy> {
    try {
      const { data } = await this.client.get(\`/api/policy/\${owner}/\${repo}\`);
      return data;
    } catch (error) {
      logger.error('Backend API getPolicy failed', { error, owner, repo });
      return { enforcement: 'blocking', rules: [] };
    }
  }

  async logAudit(auditData: any): Promise<void> {
    try {
      await this.client.post('/api/audit/log', auditData);
    } catch (error) {
      logger.error('Backend API logAudit failed', { error });
    }
  }
}
