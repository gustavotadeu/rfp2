# RFP Frontend

Frontend moderno para consumo da API RFP Automation.

## Tecnologias
- React.js (Vite)
- TailwindCSS
- Shadcn/ui
- Axios
- React Router DOM
- Zustand
- React Hook Form + Zod
- Framer Motion

## Instalação
```bash
npm install
npm run dev
```

## Configuração
- Configure a URL da API em `src/api/axios.ts`.

## Scripts
- `npm run dev` — roda em modo desenvolvimento
- `npm run build` — build para produção

## Estrutura de Pastas
```
frontend/
├── public/
├── src/
│   ├── api/
│   ├── assets/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── routes/
│   ├── styles/
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── tailwind.config.js
├── package.json
└── README.md
```

## Funcionalidades
- Login JWT
- CRUD de RFPs, Propostas, Fornecedores, BoM, Usuários
- Upload de arquivos
- Listagens com filtros, paginação e busca
- Feedback visual (toasts, loaders, mensagens)
- Layout responsivo e moderno

## Melhorias Futuras
- Dark mode
- Dashboard com gráficos
- Notificações em tempo real
- Perfis avançados

---

> Para dúvidas ou sugestões, entre em contato.
