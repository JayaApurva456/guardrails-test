import { logger } from '../config/logger';

export interface AuditLogData {
  scanId: string;
  repository: string;
  prNumber: number;
  commitSha: string;
  violationsFound: number;
  blockingCount: number;
  copilotDetected: boolean;
  duration: number;
  status: string;
  error?: string;
}

export class AuditLogger {
  async logScan(data: AuditLogData): Promise<void> {
    logger.info('Audit log entry', data);
    
    // In production, send to backend API
    // await backendClient.logAudit(data);
  }
}
