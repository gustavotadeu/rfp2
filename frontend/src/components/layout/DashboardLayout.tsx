import React from "react";
import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

const DashboardLayout = () => {
  const { nome, perfil, logout } = useAuth();
  const menu = [
    { label: "RFPs", to: "/" },
    ...(perfil === "admin"
      ? [
          { label: "Fornecedores", to: "/fornecedores" },
          { label: "Usuários", to: "/usuarios" },
          { label: "Config IA", to: "/admin/config/providers" },
        ]
      : []),
  ];
  return (
    <div className="min-h-screen flex bg-gradient-to-br from-background via-white to-primary/10">
      <aside className="w-64 min-h-screen hidden md:flex flex-col bg-white/80 backdrop-blur-xl shadow-xl border-r border-slate-200 relative z-10">
        <div className="h-16 flex items-center justify-center font-bold text-2xl tracking-tight text-primary border-b border-slate-100 drop-shadow-sm select-none">
          <div>
            <span className="bg-blue-900 bg-clip-text text-transparent">
              RFP System
            </span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {menu.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-4 py-2 rounded-xl font-medium transition-all duration-200 shadow-sm ${
                  isActive
                    ? "bg-blue-900 scale-105 text-white"
                    : "text-gray-700 hover:bg-primary/10 hover:scale-105"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 min-h-screen flex flex-col">
        <header className="h-16 bg-white/80 border-b flex items-center justify-end px-4 md:px-8 gap-4 shadow-lg backdrop-blur-xl sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-blue-700 font-medium">
              Olá,
            </span>
            <span className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-blue-900 flex items-center justify-center text-white font-bold text-lg shadow-md">
                {nome?.[0]?.toUpperCase() || "U"}
              </span>
              <button
                onClick={() => (window.location.href = "/perfil")}
                className="text-blue-700 font-semibold max-w-[120px] truncate  hover:text-accent transition"
                title="Editar perfil"
              >
                {nome}
              </button>
              <span className="text-xs px-2 py-1 bg-primary/10 text-blue-700 rounded-full ml-1">
                {perfil}
              </span>
            </span>
            <button
              onClick={logout}
              className="ml-4 px-4 py-2 rounded-lg bg-blue-900  text-white font-semibold shadow hover:brightness-110 active:scale-95 transition-all border-0"
            >
              Logout
            </button>
          </div>
        </header>
        <section className="flex-1 p-4 md:p-8 bg-transparent">
          <Outlet />
        </section>
      </main>
    </div>
  );
};

export default DashboardLayout;
