import React, { useState, useEffect } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';

const ProfilePage: React.FC = () => {
  const { nome, perfil } = useAuth();
  const [form, setForm] = useState({ nome: '', senha: '', novaSenha: '', confirmarSenha: '' });
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setForm(f => ({ ...f, nome: nome || '' }));
  }, [nome]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (form.novaSenha && form.novaSenha !== form.confirmarSenha) {
      setError('Nova senha e confirmação não coincidem.');
      return;
    }
    try {
      await api.put('/users/me', {
        nome: form.nome,
        senha_atual: form.senha,
        nova_senha: form.novaSenha || undefined,
      });
      setSuccess('Perfil atualizado com sucesso!');
      setForm({ ...form, senha: '', novaSenha: '', confirmarSenha: '' });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao atualizar perfil.');
    }
  };

  return (
    <div className="max-w-lg mx-auto bg-white p-8 rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Meu Perfil</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1">Nome</label>
          <input name="nome" value={form.nome} onChange={handleChange} className="w-full border px-3 py-2 rounded" />
        </div>
        <div>
          <label className="block mb-1">Senha atual</label>
          <input name="senha" type="password" value={form.senha} onChange={handleChange} className="w-full border px-3 py-2 rounded" />
        </div>
        <div>
          <label className="block mb-1">Nova senha</label>
          <input name="novaSenha" type="password" value={form.novaSenha} onChange={handleChange} className="w-full border px-3 py-2 rounded" />
        </div>
        <div>
          <label className="block mb-1">Confirmar nova senha</label>
          <input name="confirmarSenha" type="password" value={form.confirmarSenha} onChange={handleChange} className="w-full border px-3 py-2 rounded" />
        </div>
        <button type="submit" className="bg-primary text-white px-4 py-2 rounded">Salvar</button>
        {success && <div className="text-green-600 mt-2">{success}</div>}
        {error && <div className="text-red-500 mt-2">{error}</div>}
      </form>
    </div>
  );
};

export default ProfilePage;
