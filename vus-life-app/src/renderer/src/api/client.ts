/**
 * Axios HTTP client configuration for FastAPI backend.
 */

import axios from 'axios'
import type { AxiosError, AxiosInstance } from 'axios'

const API_BASE_URL = 'http://localhost:18000'

/**
 * Create configured Axios instance.
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 300 seconds – prediction calls can take up to 5 min
})

/**
 * Request interceptor for error handling.
 */
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor for error handling.
 */
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    // Handle network errors
    if (!error.response) {
      const errorMessage = error.code === 'ECONNREFUSED'
        ? 'Unable to connect to backend server. Make sure the backend is running on http://localhost:18000'
        : error.message || 'Unable to connect to backend server'
      console.error('Network error:', error.code, error.message)
      throw new Error(errorMessage)
    }

    // Handle HTTP errors
    const status = error.response.status
    const responseData = error.response.data as { detail?: string }
    const message = responseData?.detail || error.message

    if (status >= 500) {
      console.error('Server error:', message)
      throw new Error('Server error. Please try again later.')
    }

    if (status >= 400) {
      console.error('Client error:', message)
      throw new Error(message || 'Request failed')
    }

    return Promise.reject(error)
  }
)
