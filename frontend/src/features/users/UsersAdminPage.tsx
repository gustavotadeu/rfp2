import React, { useEffect, useState } from 'react';
import api from '../../api/axios';
import { useAuth } from '../../hooks/useAuth';

interface User {
  id: number;
  nome: string;
  email: string;
  perfil: string;
  ativo: boolean;
}

const UsersAdminPage: React.FC = () => {
  const { perfil } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ nome: '', email: '', senha: '', perfil: 'editor' });
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (perfil === 'admin') fetchUsers();
  }, [perfil]);

  const fetchUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/users/');
      setUsers(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  if (perfil !== 'admin') {
    return <div className="p-8 text-red-500">Acesso negado</div>;
  }

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await api.post('/users/', form);
      setSuccess('Usuário criado com sucesso!');
      setForm({ nome: '', email: '', senha: '', perfil: 'editor' });
      fetchUsers();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let msg = 'Erro ao criar usuário';
      if (Array.isArray(detail)) {
        msg = detail.map((d: any) => d.msg).join('; ');
      } else if (typeof detail === 'string') {
        msg = detail;
      }
      setError(msg);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Tem certeza que deseja excluir este usuário?')) return;
    setError('');
    setSuccess('');
    try {
      await api.delete(`/users/${id}/`);
      setSuccess('Usuário excluído com sucesso!');
      fetchUsers();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let msg = 'Erro ao excluir usuário';
      if (Array.isArray(detail)) {
        msg = detail.map((d: any) => d.msg).join('; ');
      } else if (typeof detail === 'string') {
        msg = detail;
      }
      setError(msg);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white p-8 rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Gerenciar Usuários</h2>
      <form onSubmit={handleCreateUser} className="flex flex-wrap gap-4 mb-6 items-end">
        <div>
          <label className="block mb-1">Nome</label>
          <input name="nome" value={form.nome} onChange={handleFormChange} className="border px-3 py-2 rounded" required />
        </div>
        <div>
          <label className="block mb-1">Email</label>
          <input name="email" type="email" value={form.email} onChange={handleFormChange} className="border px-3 py-2 rounded" required />
        </div>
        <div>
          <label className="block mb-1">Senha</label>
          <input name="senha" type="password" value={form.senha} onChange={handleFormChange} className="border px-3 py-2 rounded" required />
        </div>
        <div>
          <label className="block mb-1">Perfil</label>
          <select name="perfil" value={form.perfil} onChange={handleFormChange} className="border px-3 py-2 rounded">
            <option value="editor">Editor</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button type="submit" className="bg-primary text-white px-4 py-2 rounded">Criar</button>
      </form>
      {success && <div className="text-green-600 mb-2">{success}</div>}
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {loading ? (
        <div>Carregando...</div>
      ) : (
        <table className="min-w-full table-auto">
          <thead>
            <tr className="bg-primary/10">
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Nome</th>
              <th className="px-4 py-2 text-left">Email</th>
              <th className="px-4 py-2 text-left">Perfil</th>
              <th className="px-4 py-2 text-left">Ativo</th>
              <th className="px-4 py-2 text-left">Ações</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b hover:bg-primary/5">
                <td className="px-4 py-2">{u.id}</td>
                <td className="px-4 py-2">{u.nome}</td>
                <td className="px-4 py-2">{u.email}</td>
                <td className="px-4 py-2">{u.perfil}</td>
                <td className="px-4 py-2">{u.ativo ? 'Sim' : 'Não'}</td>
                <td className="px-4 py-2">
                  <button className="bg-red-500 text-white px-2 py-1 rounded" onClick={() => handleDelete(u.id)}>Excluir</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default UsersAdminPage;
