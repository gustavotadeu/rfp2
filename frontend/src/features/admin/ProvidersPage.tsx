import React, { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

type Provider = {
  id: number;
  name: string;
  model: string;
  api_key: string;
  is_selected: boolean;
};

const ProvidersPage: React.FC = () => {
  const { perfil } = useAuth();
  const navigate = useNavigate();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [name, setName] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (perfil !== 'admin') {
      navigate('/');
      return;
    }
    fetchProviders();
  }, [perfil, navigate]);

  const fetchProviders = async () => {
    try {
      const res = await api.get<Provider[]>('/admin/config/providers');
      setProviders(res.data);
    } catch {
      setError('Falha ao carregar provedores');
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !model || !apiKey) return;
    try {
      await api.post<Provider>('/admin/config/providers', { name, model, api_key: apiKey });
      setName(''); setModel(''); setApiKey('');
      fetchProviders();
    } catch {
      setError('Erro ao criar provedor');
    }
  };

  const handleSelect = async (id: number) => {
    try {
      await api.patch(`/admin/config/providers/${id}/select`);
      fetchProviders();
    } catch {
      setError('Erro ao selecionar provedor');
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4">Provedores de IA</h2>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      <table className="w-full mb-6 table-auto">
        <thead>
          <tr>
            <th></th>
            <th className="text-left">Nome</th>
            <th className="text-left">Modelo</th>
          </tr>
        </thead>
        <tbody>
          {providers.map(p => (
            <tr key={p.id} className="border-t">
              <td className="p-2">
                <input
                  type="radio"
                  name="prov"
                  checked={p.is_selected}
                  onChange={() => handleSelect(p.id)}
                />
              </td>
              <td className="p-2">{p.name}</td>
              <td className="p-2">{p.model}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form onSubmit={handleAdd} className="space-y-4">
        <div>
          <label className="block font-medium">Nome</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
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
        <div>
          <label className="block font-medium">API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            className="border p-2 w-full rounded"
            required
          />
        </div>
        <button type="submit" className="bg-primary text-white px-4 py-2 rounded">
          Adicionar Provedor
        </button>
      </form>
    </div>
  );
};

export default ProvidersPage;
