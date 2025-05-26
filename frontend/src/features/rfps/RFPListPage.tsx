import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import RFPCreateModal from './RFPCreateModal';
import { useAuth } from '../../hooks/useAuth';

interface RFP {
  id: number;
  nome: string;
  status: string;
  arquivo_url?: string;
  fabricante_escolhido_id?: number;
  fabricante_escolhido_nome?: string;
}

const RFPListPage = () => {
  const [rfps, setRfps] = useState<RFP[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  const navigate = useNavigate();

  const fetchRFPs = async () => {
    setLoading(true);
    try {
      const [rfpsRes, vendorsRes] = await Promise.all([api.get('/rfps'), api.get('/vendors')]);
      const vendorMap = new Map(vendorsRes.data.map((v: any) => [v.id, v.nome]));
      const enriched = rfpsRes.data.map((rfp: RFP) => ({
        ...rfp,
        fabricante_escolhido_nome: rfp.fabricante_escolhido_id ? vendorMap.get(rfp.fabricante_escolhido_id) || '' : ''
      }));
      setRfps(enriched);
    } catch {
      setError('Erro ao carregar RFPs');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (rfpId: number, filename: string) => {
    try {
      const response = await api.get(`/rfps/${rfpId}/download`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Erro ao baixar arquivo', err);
    }
  };

  const handleDelete = async (rfpId: number) => {
    if (!window.confirm('Tem certeza que deseja excluir esta RFP?')) return;
    try {
      await api.delete(`/rfps/${rfpId}`);
      fetchRFPs();
    } catch {
      setError('Erro ao excluir RFP');
    }
  };

  useEffect(() => {
    fetchRFPs();
  }, []);

  return (
    <div>
      <RFPCreateModal open={modalOpen} onClose={() => setModalOpen(false)} onCreated={fetchRFPs} />
      <div className="flex flex-col sm:flex-row justify-between items-center mb-6 gap-2">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent drop-shadow">RFPs</h2>
        <button onClick={() => setModalOpen(true)} className="bg-gradient-to-r from-primary to-accent text-white px-6 py-2 rounded-xl font-bold shadow hover:scale-105 active:scale-95 transition-all text-lg">
          + Nova RFP
        </button>
      </div>
      <div className="bg-white/90 rounded-2xl shadow-xl p-4 md:p-8">
        <div className="mb-6 flex flex-col sm:flex-row gap-2 items-center">
          <input type="text" placeholder="Buscar..." className="border px-4 py-2 rounded-lg w-full sm:w-64 focus:ring-2 focus:ring-primary" />
          <button className="bg-accent text-white px-5 py-2 rounded-lg font-semibold shadow hover:scale-105 transition">Filtrar</button>
        </div>
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-red-500 text-center py-8">{error}</div>
        ) : rfps.length === 0 ? (
          <div className="text-gray-400 text-center py-8">Nenhuma RFP encontrada.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto text-base">
              <thead>
                <tr className="bg-gradient-to-r from-primary/10 to-accent/10">
                  <th className="px-6 py-3 text-left font-bold text-primary">Nome</th>
                  <th className="px-6 py-3 text-left font-bold text-primary">Status</th>
                  <th className="px-6 py-3 text-left font-bold text-primary">Arquivo</th>
                  <th className="px-6 py-3 text-left font-bold text-primary">Fabricante</th>
                  <th className="px-6 py-3 text-left font-bold text-primary">Ações</th>
                </tr>
              </thead>
              <tbody>
                {rfps.map(rfp => (
                  <tr key={rfp.id} className="border-b border-slate-100 hover:bg-primary/5 transition">
                    <td className="px-6 py-3 font-medium">{rfp.nome}</td>
                    <td className="px-6 py-3">
                      <span className="px-3 py-1 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                        {rfp.status}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      {rfp.arquivo_url ? (
                        <button
                          onClick={() => handleDownload(rfp.id, rfp.arquivo_url?.split(/[\/]/).pop() || '')}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-primary/10 text-primary font-semibold hover:bg-primary/20 transition group"
                          title="Baixar arquivo"
                        >
                          <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4" /></svg>
                          <span className="hidden md:inline">Arquivo</span>
                        </button>
                      ) : (
                        <span className="text-gray-300 italic">—</span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      {rfp.fabricante_escolhido_nome || ''}
                    </td>
                    <td className="px-6 py-3 flex gap-2">
                      <button onClick={() => navigate(`/rfps/${rfp.id}`)} className="bg-primary text-white px-4 py-1 rounded-lg font-semibold shadow hover:bg-primary/80 transition">Ver</button>
                      <button onClick={() => handleDelete(rfp.id)} className="bg-red-500 text-white px-4 py-1 rounded-lg font-semibold shadow hover:bg-red-600 transition">Excluir</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {/* Paginação aqui (futuro) */}
      </div>
    </div>
  );
};

export default RFPListPage;
