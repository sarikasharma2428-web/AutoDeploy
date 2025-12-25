export interface SourceReference {
  id: string
  file_path: string
  start_line: number
  end_line: number
  snippet: string
}

export interface Finding {
  title: string
  severity?: 'low' | 'medium' | 'high' | 'critical'
  impact?: 'low' | 'medium' | 'high'
  effort?: 'low' | 'medium' | 'high'
  description: string
  details?: string
  reference_id: string
}

export interface TechStackBreakdown {
  languages: string[]
  frameworks: string[]
  databases: string[]
  tools: string[]
  reference_ids: string[]
}

export interface AnalysisMetadata {
  repo_url: string
  branch: string
  total_files: number
  total_lines: number
  languages: Record<string, number>
  commit?: {
    sha?: string
    message?: string
    author?: string
    date?: string
  }
}

export interface AnalysisResponse {
  summary: string
  summary_references: string[]
  tech_stack: TechStackBreakdown
  security_findings: Finding[]
  code_smells: Finding[]
  improvement_plan: Finding[]
  devops_recommendations: Finding[]
  metadata: AnalysisMetadata
  source_references: SourceReference[]
}

export interface AnalyzeRequestPayload {
  repo_url: string
  branch?: string
  include_tests?: boolean
}
