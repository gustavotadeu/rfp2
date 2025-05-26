import axiosInstance from './axios'; // Assuming axios instance is in axios.ts

// TypeScript Interfaces mirroring Pydantic Schemas
export interface AIPrompt {
  id: number;
  name: string;
  description?: string | null;
  prompt_text: string;
  created_at: string; // Typically ISO string
  updated_at: string; // Typically ISO string
}

export interface AIPromptCreateData {
  name: string;
  description?: string | null;
  prompt_text: string;
}

export interface AIPromptUpdateData {
  name?: string;
  description?: string | null;
  prompt_text?: string;
}

const API_URL = '/admin/config/prompts';

// API Service Functions
export const listPrompts = async (): Promise<AIPrompt[]> => {
  const response = await axiosInstance.get<AIPrompt[]>(API_URL);
  return response.data;
};

export const getPrompt = async (id: number): Promise<AIPrompt> => {
  const response = await axiosInstance.get<AIPrompt>(`${API_URL}/${id}`);
  return response.data;
};

export const createPrompt = async (data: AIPromptCreateData): Promise<AIPrompt> => {
  const response = await axiosInstance.post<AIPrompt>(API_URL, data);
  return response.data;
};

export const updatePrompt = async (id: number, data: AIPromptUpdateData): Promise<AIPrompt> => {
  const response = await axiosInstance.put<AIPrompt>(`${API_URL}/${id}`, data);
  return response.data;
};

export const deletePrompt = async (id: number): Promise<{ ok: boolean; detail: string }> => {
  const response = await axiosInstance.delete<{ ok: boolean; detail: string }>(`${API_URL}/${id}`);
  return response.data;
};
