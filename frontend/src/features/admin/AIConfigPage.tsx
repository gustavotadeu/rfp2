import React, { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

type Config = { id: number; provider: string; model: string; };

const AIConfigPage: React.FC = () => {
  const { perfil } = useAuth();
  const navigate = useNavigate();
  const [provider, setProvider] = useState('');
  const [model, setModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (perfil !== 'admin') {
      navigate('/');
      return;
    }
    const fetchConfig = async () => {
      try {
        const res = await api.get<Config>('/admin/config/ai');
        setProvider(res.data.provider);
        setModel(res.data.model);
      } catch (error: any) {
        if (error.response?.status !== 404) {
          setError('Não foi possível carregar configuração');
        }
      }
    };
    fetchConfig();
  }, [perfil, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      await api.post<Config>('/admin/config/ai', { provider, model });
      setSuccess('Configuração salva com sucesso');
    } catch {
      setError('Erro ao salvar configuração');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-lg mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Configuração de IA</h2>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {success && <div className="text-green-500 mb-2">{success}</div>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block font-medium">Provedor</label>
          <input
            type="text"
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="border p-2 w-full rounded"
            required
          />
        </div>
        <div>
          <label className="block font-medium">Modelo</label>
          <input
            type="text"
            value={model}
            onChange={e => setModel(e.target.value)}
            className="border p-2 w-full rounded"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-primary text-white px-4 py-2 rounded"
        >
          {loading ? 'Salvando...' : 'Salvar'}
        </button>
      </form>
    </div>
  );
};

export default AIConfigPage;
