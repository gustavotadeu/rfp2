import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import api from '../../api/axios';

const schema = z.object({
  nome: z.string().min(3, 'Nome obrigatório'),
  arquivo: z.any().refine(
    (fileList) => fileList && fileList.length > 0 && fileList[0] instanceof File && fileList[0].size > 0,
    'Arquivo obrigatório'
  ),
});

type FormData = z.infer<typeof schema>;

interface RFPCreateModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const RFPCreateModal: React.FC<RFPCreateModalProps> = ({ open, onClose, onCreated }) => {
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset } = useForm<FormData>({
    resolver: zodResolver(schema)
  });
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const onSubmit = async (data: FormData) => {
    setError('');
    setUploadProgress(null);
    try {
      // 1. Cria a RFP sem arquivo
      const rfpRes = await api.post('/rfps', {
        nome: data.nome
      });
      // Corrigir: garantir que o ID venha corretamente
      const rfpId = rfpRes.data?.id || rfpRes.data?.rfp?.id;
      if (!rfpId || rfpId === 'undefined') {
        setError('Erro ao obter o ID da RFP criada. Não é possível enviar o arquivo.');
        setUploadProgress(null);
        return;
      }
      // 2. Faz upload do arquivo
      const uploadData = new FormData();
      uploadData.append('file', data.arquivo[0]);
      await api.post(`/rfps/${rfpId}/upload`, uploadData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            setUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
          }
        },
      });
      setUploadProgress(100);
      setTimeout(() => setUploadProgress(null), 800);
      onCreated();
      onClose();
      reset();
    } catch (err: any) {
      setUploadProgress(null);
      setError(err?.response?.data?.detail || 'Erro ao criar RFP.');
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/40 z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md relative animate-fadeIn">
        <button className="absolute top-4 right-4 text-gray-400 hover:text-primary text-xl font-bold" onClick={onClose}>&times;</button>
        <h3 className="text-2xl font-bold mb-6 text-primary">Nova RFP</h3>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" encType="multipart/form-data">
          <div>
            <label className="block font-medium mb-1">Nome</label>
            <input {...register('nome')} className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary" />
            {errors.nome && <span className="text-red-500 text-sm">{errors.nome.message}</span>}
          </div>
          <div>
            <label className="block font-medium mb-1">Arquivo da RFP</label>
            <input type="file" accept=".pdf,.doc,.docx,.xlsx,.xls" {...register('arquivo')} className="w-full border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary/90 file:text-white file:font-semibold hover:file:bg-primary" />
            {errors.arquivo && <span className="text-red-500 text-sm">{String(errors.arquivo.message)}</span>}
          </div>
          {error && <div className="text-red-500 text-sm">{error}</div>}
          {uploadProgress !== null && (
            <div className="w-full bg-gray-200 rounded-full h-3 mb-2 overflow-hidden">
              <div className="bg-gradient-to-r from-primary to-accent h-3 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
            </div>
          )}
          <button type="submit" disabled={isSubmitting || uploadProgress !== null} className="w-full bg-gradient-to-r from-primary to-accent text-white py-2 rounded-xl font-bold shadow hover:scale-105 active:scale-95 transition-all mt-2 disabled:opacity-60">
            {uploadProgress !== null ? `Enviando... ${uploadProgress}%` : isSubmitting ? 'Salvando...' : 'Criar RFP'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default RFPCreateModal;
