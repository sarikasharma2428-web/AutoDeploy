import axios from 'axios'

import { AnalysisResponse, AnalyzeRequestPayload } from '../types'

const API_BASE_URL =
  import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  analyzeRepository: async (payload: AnalyzeRequestPayload): Promise<AnalysisResponse> => {
    const response = await api.post('/api/repo/analyze', payload)
    return response.data
  },
}

export default api
