import React, { useEffect, useState } from 'react';
import api from '../../../api/axios';

interface VendorMatch {
  vendor: string;
  score: number;
  motivo: string;
  vendor_id?: number;
}

interface Props {
  rfpId: number;
  savedAnalysis?: string;
  selectedVendorId?: number;
  onSave: (analysis: string) => void;
  onSelectVendor: (vendorId: number) => void;
}

const VendorMatchAnalysis: React.FC<Props> = ({ rfpId, savedAnalysis, selectedVendorId, onSave, onSelectVendor }) => {
  const [matches, setMatches] = useState<VendorMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(selectedVendorId ?? null);
  const [analysisJson, setAnalysisJson] = useState('');
  const [vendorList, setVendorList] = useState<{ id: number; nome: string }[]>([]);

  useEffect(() => {
    setSelectedId(selectedVendorId ?? null);
  }, [selectedVendorId]);

  useEffect(() => {
    api.get('/vendors')
      .then(res => setVendorList(res.data))
      .catch(err => console.error('Erro ao carregar vendors', err));
  }, []);

  useEffect(() => {
    if (savedAnalysis && vendorList.length) {
      try {
        const parsed = JSON.parse(savedAnalysis) as VendorMatch[];
        // Enriquecer vendor_id se faltante
        parsed.forEach(item => {
          if (item.vendor_id == null) {
            const v = vendorList.find(v => v.nome === item.vendor);
            if (v) item.vendor_id = v.id;
          }
        });
        parsed.sort((a, b) => b.score - a.score);
        setMatches(parsed);
      } catch {
        setMatches([]);
      }
    } else {
      setMatches([]);
      setAnalysisJson('');
    }
  }, [rfpId, savedAnalysis, vendorList]);

  const handleSave = () => {
    onSave(analysisJson);
  };

  const handleSelect = (vendorId: number) => {
    setSelectedId(vendorId);
    onSelectVendor(vendorId);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/rfps/${rfpId}/vendors-matching`);
      const sorted = res.data.sort((a: VendorMatch, b: VendorMatch) => b.score - a.score);
      setMatches(sorted);
      setAnalysisJson(JSON.stringify(sorted));
    } catch {
      setError('Erro ao obter análise de vendors');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Analisando aderência dos vendors...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div>
      <h3 className="font-bold mb-4">Análise de Aderência dos Vendors</h3>
      {!matches.length && !savedAnalysis && (
        <button className="bg-primary text-white px-4 py-2 rounded mb-4" onClick={handleAnalyze}>
          Fazer análise de vendors
        </button>
      )}
      {matches.length > 0 && (
        <>
          <table className="min-w-full table-auto mb-4">
            <thead>
              <tr>
                <th>Fabricante</th>
                <th>Pontuação</th>
                <th>Motivo</th>
                <th>Selecionar</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((v, idx) => (
                <tr key={v.vendor} className={selectedId === v.vendor_id ? 'bg-green-100' : ''}>
                  <td className="font-semibold">{v.vendor}</td>
                  <td className="text-center">{v.score}</td>
                  <td>{v.motivo}</td>
                  <td>
                    <button
                      className={`px-2 py-1 rounded ${selectedId === v.vendor_id ? 'bg-green-400 text-white' : 'bg-gray-200'}`}
                      onClick={() => handleSelect(v.vendor_id!)}
                      disabled={selectedId === v.vendor_id}
                    >Selecionar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!savedAnalysis && (
            <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={handleSave}>Salvar análise no dossiê</button>
          )}
        </>
      )}
    </div>
  );
};

export default VendorMatchAnalysis;
