import adminApiClient from './client';
import { ApiResponse } from '@/types';
import { AdminLoginRequest, AdminLoginResponse } from '@/types/admin';

export const adminAuthApi = {
  login: async (data: AdminLoginRequest): Promise<ApiResponse<AdminLoginResponse>> => {
    const response = await adminApiClient.post<ApiResponse<AdminLoginResponse>>(
      '/admin/login',
      data
    );
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Admin logout is client-side only (clear token)
    // Server-side logout can be added if needed
  },

  getCurrentAdmin: async (): Promise<ApiResponse<AdminLoginResponse['admin']>> => {
    const response = await adminApiClient.get<ApiResponse<AdminLoginResponse['admin']>>(
      '/admin/me'
    );
    return response.data;
  },
};
