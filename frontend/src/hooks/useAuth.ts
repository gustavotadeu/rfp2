import { useCallback } from 'react';

export function useAuth() {
  const token = localStorage.getItem('token');
  const nome = localStorage.getItem('nome');
  const perfil = localStorage.getItem('perfil');
  const isAuthenticated = !!token;

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('nome');
    localStorage.removeItem('perfil');
    window.location.href = '/login';
  }, []);

  return { isAuthenticated, token, nome, perfil, logout };
}
