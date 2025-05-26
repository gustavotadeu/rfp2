import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import api from '../../api/axios';
import { useNavigate } from 'react-router-dom';

const schema = z.object({
  username: z.string().email({ message: 'E-mail inválido' }),
  password: z.string().min(3, { message: 'Senha obrigatória' })
});

type LoginForm = z.infer<typeof schema>;

const LoginPage = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({ resolver: zodResolver(schema) });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const onSubmit = async (data: LoginForm) => {
    setLoading(true);
    setError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', data.username);
      formData.append('password', data.password);
      const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('perfil', response.data.perfil);
      localStorage.setItem('nome', response.data.nome);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Falha ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6 text-center text-primary">Login</h1>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-700">Email</label>
            <input type="email" autoComplete="username" {...register('username')} className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary ${errors.username ? 'border-red-500' : ''}`} />
            {errors.username && <span className="text-red-500 text-xs">{errors.username.message}</span>}
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-700">Senha</label>
            <input type="password" autoComplete="current-password" {...register('password')} className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary ${errors.password ? 'border-red-500' : ''}`} />
            {errors.password && <span className="text-red-500 text-xs">{errors.password.message}</span>}
          </div>
          <button disabled={loading} type="submit" className="w-full bg-primary text-white py-2 rounded-lg font-semibold hover:bg-blue-700 transition disabled:opacity-60 disabled:cursor-not-allowed">
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
          {error && <div className="text-red-500 text-center text-sm mt-2">{error}</div>}
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
