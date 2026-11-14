import { apiRequest } from './client';
import { getFriendlyErrorMessage } from '../lib/labels.js';

export interface ExtractionField {
  value: string | number | null;
  confidence: number;
  corrected?: boolean;
}

export interface BillResponse {
  bill_id: number;
  user_id: number;
  file_url: string;
  file_type: string;
  parse_status: string;
  raw_text?: string | null;
  extraction_json?: Record<string, ExtractionField> | null;
  corrected_fields?: Record<string, unknown> | null;
  uploaded_at: string;
}

export interface ServiceResponse {
  service_id: number;
  appliance_id: number;
  due_date: string;
  status: string;
  completed_on?: string | null;
  cost?: number | null;
  guidance_label?: string | null;
  note?: string | null;
}

export interface ApplianceResponse {
  appliance_id: number;
  user_id: number;
  category_id: number;
  bill_id?: number | null;
  product_name: string;
  brand?: string | null;
  model_number?: string | null;
  seller?: string | null;
  price?: number | null;
  purchase_date: string;
  warranty_months: number;
  warranty_end_date: string;
  estimated_value?: number | null;
  updated_at?: string | null;
  services: ServiceResponse[];
}

export interface ApplianceCreateRequest {
  bill_id?: number | null;
  category_id: number;
  product_name: string;
  brand?: string | null;
  model_number?: string | null;
  seller?: string | null;
  price?: number | null;
  purchase_date: string;
  warranty_months: number;
  corrected_fields?: Record<string, unknown> | null;
}

export interface ReminderResponse {
  reminder_id: number;
  user_id: number;
  appliance_id?: number | null;
  service_id?: number | null;
  liability_id?: number | null;
  goal_id?: number | null;
  type: string;
  remind_on: string;
  message?: string | null;
  sent: boolean;
}

export async function uploadBill(file: File): Promise<BillResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const token = localStorage.getItem('vault_token');
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/bills`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    let detail = `Upload failed with status: ${response.status}`;
    try {
      const err = await response.json();
      if (err.detail) detail = typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
    } catch {
      // fallback
    }
    throw new Error(getFriendlyErrorMessage(detail));
  }

  return response.json();
}

export async function getBill(billId: number): Promise<BillResponse> {
  return apiRequest<BillResponse>(`/bills/${billId}`);
}

export async function fetchAppliances(): Promise<ApplianceResponse[]> {
  return apiRequest<ApplianceResponse[]>('/appliances');
}

export async function confirmAppliance(data: ApplianceCreateRequest): Promise<ApplianceResponse> {
  return apiRequest<ApplianceResponse>('/appliances', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

export async function markServiceDone(serviceId: number): Promise<ServiceResponse> {
  return apiRequest<ServiceResponse>(`/services/${serviceId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'done', completed_on: new Date().toISOString().split('T')[0] }),
  });
}

export async function fetchReminders(): Promise<ReminderResponse[]> {
  return apiRequest<ReminderResponse[]>('/reminders');
}
