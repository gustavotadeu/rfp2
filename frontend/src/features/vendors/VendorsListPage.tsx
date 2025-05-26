import React, { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';

interface Vendor {
  id: number;
  nome: string;
  tecnologias?: string;
  produtos?: string;
  certificacoes?: string;
  requisitos_atendidos?: string;
}

const VendorsListPage: React.FC = () => {
  const { perfil } = useAuth();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState<Vendor | null>(null);
  const [nome, setNome] = useState('');
  const [tecnologias, setTecnologias] = useState('');
  const [produtos, setProdutos] = useState('');
  const [certificacoes, setCertificacoes] = useState('');
  const [requisitosAtendidos, setRequisitosAtendidos] = useState('');

  useEffect(() => {
    if (perfil !== 'admin') return;
    fetchVendors();
  }, [perfil]);

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const res = await api.get('/vendors');
      setVendors(res.data);
    } catch {
      setError('Erro ao carregar fornecedores');
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditingVendor(null);
    setNome('');
    setTecnologias('');
    setProdutos('');
    setCertificacoes('');
    setRequisitosAtendidos('');
    setModalOpen(true);
  };

  const openEditModal = (vendor: Vendor) => {
    setEditingVendor(vendor);
    setNome(vendor.nome || '');
    setTecnologias(vendor.tecnologias || '');
    setProdutos(vendor.produtos || '');
    setCertificacoes(vendor.certificacoes || '');
    setRequisitosAtendidos(vendor.requisitos_atendidos || '');
    setModalOpen(true);
  };

  const deleteVendor = async (id: number) => {
    if (!window.confirm('Deseja excluir este fornecedor?')) return;
    try {
      await api.delete(`/vendors/${id}`);
      fetchVendors();
    } catch {
      setError('Erro ao excluir fornecedor');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      nome,
      tecnologias,
      produtos,
      certificacoes,
      requisitos_atendidos: requisitosAtendidos,
    };
    try {
      if (editingVendor) {
        await api.put(`/vendors/${editingVendor.id}`, payload);
      } else {
        await api.post('/vendors', payload);
      }
      setModalOpen(false);
      fetchVendors();
    } catch (err: any) {
      console.error('Salvar fornecedor erro:', err);
      setError(err.response?.data?.detail || err.response?.data || err.message || 'Erro ao salvar fornecedor');
    }
  };

  if (perfil !== 'admin') {
    return <div className="p-8 text-red-500">Acesso negado</div>;
  }

  return (
    <div className="p-8 bg-white rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Gerenciar Fornecedores</h2>
        <button className="bg-primary text-white px-4 py-2 rounded" onClick={openAddModal}>Adicionar</button>
      </div>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {loading ? (
        <div>Carregando...</div>
      ) : (
        <table className="min-w-full table-auto">
          <thead>
            <tr className="bg-primary/10">
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Nome</th>
              <th className="px-4 py-2">Ações</th>
            </tr>
          </thead>
          <tbody>
            {vendors.map(v => (
              <tr key={v.id} className="border-b hover:bg-primary/5">
                <td className="px-4 py-2">{v.id}</td>
                <td className="px-4 py-2">{v.nome}</td>
                <td className="px-4 py-2 flex gap-2 justify-center">
                  <button className="bg-yellow-400 px-2 py-1 rounded" onClick={() => openEditModal(v)}>Editar</button>
                  <button className="bg-red-500 text-white px-2 py-1 rounded" onClick={() => deleteVendor(v.id)}>Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {modalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg w-full max-w-md">
            <h3 className="text-xl font-semibold mb-4">{editingVendor ? 'Editar' : 'Adicionar'} Fornecedor</h3>
            <form onSubmit={handleSubmit}>
              <input
                type="text"
                value={nome}
                onChange={e => setNome(e.target.value)}
                placeholder="Nome do fornecedor"
                className="w-full border px-3 py-2 rounded mb-2"
              />
              <input
                type="text"
                value={tecnologias}
                onChange={e => setTecnologias(e.target.value)}
                placeholder="Tecnologias"
                className="w-full border px-3 py-2 rounded mb-2"
              />
              <input
                type="text"
                value={produtos}
                onChange={e => setProdutos(e.target.value)}
                placeholder="Produtos"
                className="w-full border px-3 py-2 rounded mb-2"
              />
              <input
                type="text"
                value={certificacoes}
                onChange={e => setCertificacoes(e.target.value)}
                placeholder="Certificações"
                className="w-full border px-3 py-2 rounded mb-2"
              />
              <input
                type="text"
                value={requisitosAtendidos}
                onChange={e => setRequisitosAtendidos(e.target.value)}
                placeholder="Requisitos atendidos"
                className="w-full border px-3 py-2 rounded mb-4"
              />
              <div className="flex justify-end gap-2">
                <button type="button" className="px-4 py-2" onClick={() => setModalOpen(false)}>Cancelar</button>
                <button type="submit" className="bg-primary text-white px-4 py-2 rounded">{editingVendor ? 'Salvar' : 'Adicionar'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default VendorsListPage;
