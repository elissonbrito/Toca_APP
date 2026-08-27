#!/bin/bash
# Toca do Espanhol - Script de Inicialização

set -e

echo ""
echo "🍖 ======================================"
echo "   Toca do Espanhol — Sistema de Gestão"
echo "   ======================================"
echo ""

# Check if .env exists in backend
if [ ! -f "./backend/.env" ]; then
  echo "⚠️  Criando .env a partir do .env.example..."
  cp ./backend/.env.example ./backend/.env
  echo "✅ .env criado. Edite conforme necessário."
fi

echo "🐳 Iniciando serviços Docker..."
docker-compose up -d --build

echo ""
echo "⏳ Aguardando backend inicializar..."
sleep 10

echo ""
echo "✅ Sistema iniciado com sucesso!"
echo ""
echo "🌐 URLs:"
echo "   Frontend:  http://localhost"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/"
echo ""
echo "🔑 Login padrão:"
echo "   Email: admin@toca.com"
echo "   Senha: 123456"
echo ""
echo "📋 Outros usuários (senha: 123456):"
echo "   gerente@toca.com   | parrilla@toca.com"
echo "   garcom@toca.com    | caixa@toca.com"
echo "   cozinha@toca.com   | recepcao@toca.com"
echo ""
