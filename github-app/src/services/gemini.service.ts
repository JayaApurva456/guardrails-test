import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import { logger } from '../config/logger';

export interface SecurityVulnerability {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  line: number;
  column?: number;
  description: string;
  explanation: string;
  suggestedFix: string;
  cwe?: string;
  owasp?: string;
  confidence: number;
}

export interface GeminiAnalysisResult {
  vulnerabilities: SecurityVulnerability[];
  summary: string;
  analysisTime: number;
}

export class GeminiService {
  private model: GenerativeModel;
  private readonly MODEL_NAME = 'gemini-1.5-pro';

  constructor(apiKey: string) {
    const genAI = new GoogleGenerativeAI(apiKey);
    this.model = genAI.getGenerativeModel({
      model: this.MODEL_NAME,
      generationConfig: {
        temperature: 0.2,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      },
    });
  }

  /**
   * Analyze code for security vulnerabilities using Gemini AI
   */
  async analyzeSecurityWithGemini(
    code: string,
    filename: string,
    language: string
  ): Promise<GeminiAnalysisResult> {
    const startTime = Date.now();

    try {
      const prompt = this.buildSecurityPrompt(code, filename, language);
      const result = await this.model.generateContent(prompt);
      const response = result.response.text();
      
      const vulnerabilities = this.parseVulnerabilities(response);
      
      logger.info(`Gemini analysis completed for ${filename}`, {
        vulnerabilities: vulnerabilities.length,
        duration: Date.now() - startTime,
      });

      return {
        vulnerabilities,
        summary: this.generateSummary(vulnerabilities),
        analysisTime: Date.now() - startTime,
      };
    } catch (error) {
      logger.error('Gemini analysis failed', { error, filename });
      throw new Error(`Gemini analysis failed: ${error.message}`);
    }
  }

  /**
   * Validate static analysis findings to reduce false positives
   */
  async validateStaticFindings(
    findings: any[],
    code: string,
    filename: string
  ): Promise<any[]> {
    if (findings.length === 0) return [];

    try {
      const prompt = `
You are a security expert validating potential vulnerabilities.

Code file: ${filename}
\`\`\`
${code}
\`\`\`

Static analysis found these potential issues:
${JSON.stringify(findings, null, 2)}

For each finding, determine if it's a real vulnerability or false positive.
Consider:
- Context of the code
- Whether it's actually exploitable
- If there are mitigating factors

Return JSON array with isValid (true/false) and reasoning:
{
  "validations": [
    {
      "findingId": 0,
      "isValid": true,
      "confidence": 0.95,
      "reasoning": "This is a real SQL injection vulnerability because..."
    }
  ]
}
`;

      const result = await this.model.generateContent(prompt);
      const response = result.response.text();
      const validation = this.parseValidation(response);

      return findings.filter((_, idx) => {
        const v = validation.validations[idx];
        return v && v.isValid;
      });
    } catch (error) {
      logger.error('Validation failed, keeping all findings', { error });
      return findings; // Keep all if validation fails
    }
  }

  /**
   * Generate secure code fix suggestion
   */
  async generateFix(
    vulnerability: SecurityVulnerability,
    originalCode: string,
    language: string
  ): Promise<string> {
    try {
      const prompt = `
You are a security expert. Generate a secure code fix.

Language: ${language}
Vulnerability: ${vulnerability.type}
Issue: ${vulnerability.description}

Original code:
\`\`\`${language}
${originalCode}
\`\`\`

Provide ONLY the fixed code (no explanations), properly formatted.
`;

      const result = await this.model.generateContent(prompt);
      return this.extractCodeFromResponse(result.response.text(), language);
    } catch (error) {
      logger.error('Fix generation failed', { error });
      return 'Unable to generate automatic fix. Please review manually.';
    }
  }

  /**
   * Build comprehensive security analysis prompt
   */
  private buildSecurityPrompt(code: string, filename: string, language: string): string {
    return `
You are an expert security auditor analyzing code for vulnerabilities.

File: ${filename}
Language: ${language}

Analyze this code for OWASP Top 10 and CWE vulnerabilities:
\`\`\`${language}
${code}
\`\`\`

Focus on:
1. **Injection** (SQL, Command, Code)
2. **Broken Authentication**
3. **Sensitive Data Exposure** (hardcoded secrets, passwords)
4. **XML External Entities (XXE)**
5. **Broken Access Control**
6. **Security Misconfiguration**
7. **Cross-Site Scripting (XSS)**
8. **Insecure Deserialization**
9. **Using Components with Known Vulnerabilities**
10. **Insufficient Logging & Monitoring**

For each vulnerability found, provide:
- Type of vulnerability
- Severity (critical/high/medium/low)
- Line number where it occurs
- Clear description
- Detailed explanation of why it's dangerous
- Specific fix suggestion with code example
- CWE ID if applicable
- OWASP category
- Confidence score (0-1)

Return ONLY valid JSON (no markdown, no explanations):
{
  "vulnerabilities": [
    {
      "type": "SQL Injection",
      "severity": "critical",
      "line": 42,
      "description": "User input directly concatenated into SQL query",
      "explanation": "This allows attackers to inject malicious SQL code...",
      "suggestedFix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
      "cwe": "CWE-89",
      "owasp": "A03:2021 - Injection",
      "confidence": 0.95
    }
  ]
}

If no vulnerabilities found, return: {"vulnerabilities": []}
`;
  }

  /**
   * Parse vulnerabilities from Gemini response
   */
  private parseVulnerabilities(response: string): SecurityVulnerability[] {
    try {
      // Extract JSON from response (handle markdown code blocks)
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        logger.warn('No JSON found in Gemini response');
        return [];
      }

      const parsed = JSON.parse(jsonMatch[0]);
      return parsed.vulnerabilities || [];
    } catch (error) {
      logger.error('Failed to parse Gemini response', { error, response });
      return [];
    }
  }

  /**
   * Parse validation response
   */
  private parseValidation(response: string): any {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) return { validations: [] };
      return JSON.parse(jsonMatch[0]);
    } catch (error) {
      logger.error('Failed to parse validation response', { error });
      return { validations: [] };
    }
  }

  /**
   * Extract code from Gemini response
   */
  private extractCodeFromResponse(response: string, language: string): string {
    // Try to extract code block
    const codeBlockRegex = new RegExp(`\`\`\`${language}([\\s\\S]*?)\`\`\``, 'i');
    const match = response.match(codeBlockRegex);
    
    if (match) {
      return match[1].trim();
    }

    // If no code block, return cleaned response
    return response.replace(/```/g, '').trim();
  }

  /**
   * Generate summary of vulnerabilities
   */
  private generateSummary(vulnerabilities: SecurityVulnerability[]): string {
    const critical = vulnerabilities.filter(v => v.severity === 'critical').length;
    const high = vulnerabilities.filter(v => v.severity === 'high').length;
    const medium = vulnerabilities.filter(v => v.severity === 'medium').length;
    const low = vulnerabilities.filter(v => v.severity === 'low').length;

    if (vulnerabilities.length === 0) {
      return 'No vulnerabilities detected';
    }

    return `Found ${vulnerabilities.length} vulnerabilities: ${critical} critical, ${high} high, ${medium} medium, ${low} low`;
  }
}
