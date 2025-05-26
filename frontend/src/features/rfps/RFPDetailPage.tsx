import React, { useState, useRef, useEffect } from 'react';
import api from '../../api/axios';
import { useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import VendorMatchAnalysis from './components/VendorMatchAnalysis';

const RFPDetailPage = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState<'ia'|'vendors'|'bom'|'propostas'|'escopo'>('ia');
  const [escopos, setEscopos] = useState<any[]>([]);
  const [escopoTitulo, setEscopoTitulo] = useState('');
  const [escopoDescricao, setEscopoDescricao] = useState('');
  const [escopoLoading, setEscopoLoading] = useState(false);
  const [escopoError, setEscopoError] = useState('');
  const [editingEscopoId, setEditingEscopoId] = useState<number | null>(null);
  const [bomItems, setBomItems] = useState<any[]>([]);
  const [generatingBom, setGeneratingBom] = useState(false);
  const [bomError, setBomError] = useState('');
  const [rfp, setRfp] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>('');
  const [file, setFile] = useState<File | null>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [filesError, setFilesError] = useState('');
  const [vendorAnalysisSaved, setVendorAnalysisSaved] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [proposals, setProposals] = useState<any[]>([]);
  const [proposalsError, setProposalsError] = useState('');
  const [techSections, setTechSections] = useState<Record<string,string> | null>(null);
  const [editingProposalId, setEditingProposalId] = useState<number | null>(null);
  const [techLoading, setTechLoading] = useState(false);
  const [techError, setTechError] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const fetchBom = async () => {
    if (!id) return;
    try {
      const res = await api.get(`/bom/rfp/${id}`);
      setBomItems(res.data);
    } catch (err: any) {
      setBomError('Erro ao carregar BoM');
    }
  };

  const handleGenerateBom = async () => {
    if (!id) return;
    setGeneratingBom(true);
    setBomError('');
    try {
      await api.post(`/bom/rfp/${id}/generate`);
      await fetchBom();
    } catch (err: any) {
      setBomError(err?.response?.data?.detail || 'Erro ao gerar BoM via IA');
    } finally {
      setGeneratingBom(false);
    }
  };

  const fetchRfp = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get(`/rfps/${id}`);
      setRfp(res.data);
      if (res.data.resumo_ia) {
        setAnalysisResult(res.data.resumo_ia);
      }
    } catch (err) {
      setRfp(null);
    }
    setLoading(false);
  };

  const fetchProposals = async () => {
    if (!id) return;
    try {
      const res = await api.get(`/propostas/rfp/${id}`);
      setProposals(res.data);
      if (res.data.length > 0) {
        setEditingProposalId(res.data[0].id);
        setTechSections(res.data[0].dados_json || null);
      } else {
        setEditingProposalId(null);
        setTechSections(null);
      }
    } catch {
      setProposalsError('Erro ao carregar propostas');
    }
  };

  const fetchFiles = async () => {
    if (!id) return;
    try {
      const res = await api.get(`/rfps/${id}/files`);
      setFiles(res.data);
    } catch (err: any) {
      setFilesError('Erro ao carregar arquivos');
    }
  };

  useEffect(() => {
    fetchRfp();
    fetchProposals();
    fetchBom();
    fetchEscopos();
    fetchFiles();
    // eslint-disable-next-line
  }, [id]);

  useEffect(() => {
    if (activeTab === 'escopo') fetchEscopos();
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'ia' || activeTab === 'vendors') {
      fetchRfp();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 'bom') {
      fetchRfp();
      fetchBom();
    }
  }, [activeTab]);

  const fetchEscopos = async () => {
    if (!id) return;
    setEscopoLoading(true);
    setEscopoError('');
    try {
      const res = await api.get(`/escopos/rfp/${id}`);
      setEscopos(res.data);
    } catch (err: any) {
      setEscopoError('Erro ao carregar escopos');
    } finally {
      setEscopoLoading(false);
    }
  };

  const handleSaveEscopo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!escopoTitulo) return;
    setEscopoLoading(true);
    setEscopoError('');
    try {
      if (editingEscopoId) {
        await api.put(`/escopos/${editingEscopoId}`, { titulo: escopoTitulo, descricao: escopoDescricao });
      } else {
        await api.post(`/escopos/rfp/${id}`, { titulo: escopoTitulo, descricao: escopoDescricao });
      }
      setEscopoTitulo('');
      setEscopoDescricao('');
      setEditingEscopoId(null);
      fetchEscopos();
    } catch (err: any) {
      setEscopoError(editingEscopoId ? 'Erro ao editar escopo' : 'Erro ao adicionar escopo');
    } finally {
      setEscopoLoading(false);
    }
  };

  const handleDeleteEscopo = async (escopoId: number) => {
    if (!window.confirm('Confirmar exclusão do escopo?')) return;
    setEscopoLoading(true);
    try {
      await api.delete(`/escopos/${escopoId}`);
      fetchEscopos();
    } catch {
      setEscopoError('Erro ao excluir escopo');
    } finally {
      setEscopoLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    if (!id || id === 'undefined') {
      setUploadError('ID da RFP não encontrado. Não é possível enviar o arquivo.');
      return;
    }
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    try {
      await api.post(`/rfps/${id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      fetchRfp(); // Atualiza detalhes após upload
      fetchFiles();
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || 'Erro ao fazer upload.');
    }
  };

  const handleAnalyze = async () => {
    if (!id) return;
    setAnalyzing(true);
    try {
      const res = await api.post(`/rfps/${id}/analyze`);
      setAnalysisResult(res.data.resumo);
      await fetchRfp();
    } catch (err: any) {
      console.error('Erro ao analisar RFP', err);
    } finally {
      setAnalyzing(false);
    }
  };

  // Save vendor analysis and chosen vendor to backend
  const saveVendorAnalysis = async (analysis: string) => {
    if (!id) return;
    try {
      await api.post(`/rfps/${id}/save-vendor-analysis`, { analise: analysis });
      if (selectedVendor !== null) {
        await api.post(`/rfps/${id}/set-fabricante-escolhido`, { fabricante_escolhido_id: selectedVendor });
      }
      fetchRfp();
    } catch (err) {
      console.error('Erro ao salvar análise de vendors', err);
    }
  };

  const handleSelectVendorAPI = async (vendorId: number) => {
    setSelectedVendor(vendorId);
    if (!id) return;
    try {
      await api.post(`/rfps/${id}/set-fabricante-escolhido`, { fabricante_escolhido_id: vendorId });
      fetchRfp();
    } catch (err) {
      console.error('Erro ao definir fabricante escolhido', err);
    }
  };

  // Generate technical proposal via IA
  const handleGenerateProposal = async () => {
    if (!id) return;
    setTechLoading(true);
    setTechError('');
    try {
      const res = await api.post(`/propostas_tecnicas/rfp/${id}/gerar`);
      setTechSections(res.data);
      await fetchProposals();
    } catch {
      setTechError('Erro ao gerar proposta via IA');
    } finally {
      setTechLoading(false);
    }
  };

  // Save edited proposal
  const handleSaveProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProposalId || !techSections) return;
    setTechLoading(true);
    setTechError('');
    try {
      await api.put(`/propostas/item/${editingProposalId}`, { dados_json: techSections });
      await fetchProposals();
    } catch {
      setTechError('Erro ao salvar proposta');
    } finally {
      setTechLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-8">
      <button className="mb-4 text-primary hover:underline">Voltar</button>
      <h2 className="text-xl font-bold mb-2">Detalhes da RFP</h2>
      {/* Exibe dados reais da RFP */}
      {loading ? (
        <div>Carregando...</div>
      ) : rfp ? (
        <>
          <div className="mb-4">
            <div className="font-medium">Nome:</div>
            <div>{rfp.nome}</div>
          </div>
          <div className="mb-4">
            <div className="font-medium">Status:</div>
            <div>{rfp.status}</div>
          </div>
          <div className="mb-4">
            <div className="font-medium">Arquivo:</div>
            {rfp.arquivo_url ? (
              <a
                href={api.getUri({ url: `/uploaded_rfps/${rfp.arquivo_url.split(/[\\/]/).pop()}` })}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline"
                download
              >
                {rfp.arquivo_url.split('_').slice(2).join('_')}
              </a>
            ) : (
              <span className="text-gray-500">Nenhum arquivo enviado</span>
            )}
          </div>
          {/* Lista de uploads múltiplos */}
          <div className="mb-4">
            <div className="font-medium">Arquivos Adicionais:</div>
            {files.length > 0 ? (
              files.map(f => (
                <a
                  key={f.id}
                  href={api.getUri({ url: `/rfps/${id}/download/${f.id}` })}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-blue-600 underline"
                >
                  {f.filename}
                </a>
              ))
            ) : (
              <span className="text-gray-500">Nenhum arquivo adicional</span>
            )}
          </div>
        </>
      ) : (
        <div className="text-red-500">RFP não encontrada.</div>
      )}
      {/* Tabs */}
      <div className="flex space-x-4 border-b mb-4">
        {['ia','vendors','bom','escopo','propostas'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`px-4 py-2 ${activeTab===tab?'border-b-2 font-semibold text-primary':''}`}
          >
            {tab==='ia'? 'Análise IA' : tab==='vendors'? 'Análise Vendors' : tab==='bom'? 'BoM' : tab==='propostas' ? 'Propostas' : 'Escopo de Serviços'}
          </button>
        ))}
      </div>
      {/* Tab panels */}
      {activeTab==='ia' && (
        <>
          {/* Upload/Analyze section */}
          <div className="flex gap-4 mb-6 items-center">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.xlsx,.xls"
              ref={fileInputRef}
              className="hidden"
              onChange={handleFileChange}
            />
            <button
              className="bg-accent text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-60"
              onClick={handleUploadClick}
            >
              Upload Arquivo
            </button>
            {uploadError && <span className="text-red-500 text-sm ml-2">{uploadError}</span>}
            <button onClick={handleAnalyze} disabled={analyzing} className="bg-primary text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-60">
              {analyzing ? 'Analisando...' : 'Analisar com IA'}
            </button>
          </div>
          {/* IA result */}
          {analysisResult && (
            <div className="mb-6 bg-gray-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">Resumo da IA</h3>
              <div className="prose prose-sm max-w-full break-words whitespace-pre-wrap overflow-x-auto">
                <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{analysisResult}</ReactMarkdown>
              </div>
            </div>
          )}
        </>
      )}
      {activeTab==='vendors' && (
        <VendorMatchAnalysis
          rfpId={Number(id)}
          savedAnalysis={rfp?.analise_vendors}
          selectedVendorId={selectedVendor ?? undefined}
          onSelectVendor={handleSelectVendorAPI}
          onSave={saveVendorAnalysis}
        />
      )}
      {activeTab==='bom' && (
        <div className="mt-6">
          {/* Existing BoM section */}
          <h3 className="font-bold mb-2">Itens BoM</h3>
          <button
            className="bg-primary text-white px-4 py-2 rounded-lg font-semibold disabled:opacity-60 mb-4"
            onClick={handleGenerateBom}
            disabled={generatingBom}
          >
            {generatingBom ? 'Gerando BoM via IA...' : 'Gerar BoM via IA'}
          </button>
          {bomError && <span className="text-red-500 text-sm ml-2">{bomError}</span>}
          <div className="overflow-x-auto mt-2">
            {bomItems.length === 0 ? (
              <div className="text-gray-500">Nenhum item de BoM encontrado.</div>
            ) : (
              <table className="min-w-full border text-sm">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border px-2 py-1">Descrição</th>
                    <th className="border px-2 py-1">Modelo</th>
                    <th className="border px-2 py-1">Part Number</th>
                    <th className="border px-2 py-1">Quantidade</th>
                  </tr>
                </thead>
                <tbody>
                  {bomItems.map((item, idx) => (
                    <tr key={idx}>
                      <td className="border px-2 py-1">{item.descricao}</td>
                      <td className="border px-2 py-1">{item.modelo}</td>
                      <td className="border px-2 py-1">{item.part_number}</td>
                      <td className="border px-2 py-1">{item.quantidade}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
      {activeTab==='propostas' && (
        <>
          <div className="mt-6">
            <h3 className="font-bold mb-2">Propostas</h3>
            {proposalsError && <span className="text-red-500">{proposalsError}</span>}
            {/* Gerar Proposta via IA */}
            <button
              className="bg-primary text-white px-4 py-2 rounded-lg font-semibold mb-4"
              type="button"
              disabled={techLoading}
              onClick={handleGenerateProposal}
            >
              {techLoading ? 'Gerando proposta via IA...' : 'Gerar Proposta via IA'}
            </button>
            {!techSections ? (
              <div className="text-gray-500">Nenhuma proposta disponível.</div>
            ) : (
              <form onSubmit={handleSaveProposal} className="mt-4 space-y-4">
                {techSections && Object.entries(techSections).map(([key,value]) => (
                  <div key={key}>
                    <label className="font-semibold">{key}</label>
                    <textarea
                      className="border w-full p-2 rounded mt-1"
                      rows={4}
                      value={value}
                      onChange={e => setTechSections(s => s ? { ...s, [key]: e.target.value } : s)}
                    />
                  </div>
                ))}
                <div className="flex gap-2 mt-2">
                  <button type="submit" className="bg-primary text-white px-4 py-2 rounded" disabled={techLoading}>
                    {techLoading ? 'Salvando...' : 'Salvar Proposta'}
                  </button>
                  <button
                    type="button"
                    className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                    onClick={async () => {
                      setTechLoading(true);
                      try {
                        const resp = await api.get(`/propostas_tecnicas/rfp/${id}/download`, { responseType: 'blob' });
                        const url = window.URL.createObjectURL(new Blob([resp.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', `proposta_tecnica_rfp_${id}.docx`);
                        document.body.appendChild(link);
                        link.click();
                        link.parentNode?.removeChild(link);
                      } catch {
                        setTechError('Erro ao baixar proposta DOCX');
                      } finally {
                        setTechLoading(false);
                      }
                    }}
                  >
                    Download Proposta (DOCX)
                  </button>
                </div>
                {techError && <span className="text-red-500 text-sm">{techError}</span>}
              </form>
            )}
          </div>
        </>
      )}
      {activeTab==='escopo' && (
        <div className="mt-6">
          <h3 className="font-bold mb-2">Escopo de Serviços</h3>
          <button
            className="bg-accent text-white px-4 py-2 rounded font-semibold mb-2 w-fit"
            type="button"
            disabled={escopoLoading}
            onClick={async () => {
              setEscopoLoading(true);
              setEscopoError('');
              try {
                const res = await api.post(`/escopos/rfp/${id}/sugerir`);
                setEscopoTitulo(res.data.titulo);
                setEscopoDescricao(res.data.descricao);
              } catch (err: any) {
                setEscopoError('Erro ao sugerir escopo via IA');
              } finally {
                setEscopoLoading(false);
              }
            }}
          >
            Sugerir Escopo via IA
          </button>
          <form className="flex flex-col gap-2 mb-4" onSubmit={handleSaveEscopo}>
            <input
              type="text"
              className="border px-3 py-2 rounded"
              placeholder="Título do escopo"
              value={escopoTitulo}
              onChange={e => setEscopoTitulo(e.target.value)}
              required
            />
            <textarea
              className="border px-3 py-2 rounded"
              placeholder="Descrição do escopo (opcional)"
              value={escopoDescricao}
              onChange={e => setEscopoDescricao(e.target.value)}
              rows={5}
            />
            <div className="flex gap-2">
              <button type="submit" className="bg-primary text-white px-4 py-2 rounded font-semibold" disabled={escopoLoading}>
                {editingEscopoId ? 'Salvar Alterações' : 'Adicionar Escopo'}
              </button>
              {editingEscopoId && (
                <button type="button" className="bg-gray-300 px-4 py-2 rounded" onClick={() => { setEditingEscopoId(null); setEscopoTitulo(''); setEscopoDescricao(''); }}>
                  Cancelar
                </button>
              )}
            </div>
            {escopoError && <span className="text-red-500 text-sm">{escopoError}</span>}
          </form>
          <div className="overflow-x-auto mt-2">
            {escopoLoading ? (
              <div>Carregando...</div>
            ) : escopos.length === 0 ? (
              <div className="text-gray-500">Nenhum escopo cadastrado.</div>
            ) : (
              <table className="min-w-full border text-sm">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-2 py-1 border">Título</th>
                    <th className="px-2 py-1 border">Descrição</th>
                    <th className="px-2 py-1 border">Criado em</th>
                    <th className="px-2 py-1 border">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {escopos.map((e: any) => (
                    <tr key={e.id}>
                      <td className="border px-2 py-1 font-semibold">{e.titulo}</td>
                      <td className="border px-2 py-1 whitespace-pre-line">{e.descricao}</td>
                      <td className="border px-2 py-1">{new Date(e.created_at).toLocaleString('pt-BR')}</td>
                      <td className="border px-2 py-1">
                        <div className="flex gap-2 justify-center">
                          <button
                            className="bg-yellow-400 hover:bg-yellow-500 text-white px-3 py-1 rounded"
                            onClick={() => { setEditingEscopoId(e.id); setEscopoTitulo(e.titulo); setEscopoDescricao(e.descricao || ''); }}
                          >
                            Editar
                          </button>
                          <button
                            className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded"
                            onClick={() => handleDeleteEscopo(e.id)}
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RFPDetailPage;
