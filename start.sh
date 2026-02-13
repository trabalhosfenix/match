#!/bin/bash
# start.sh

echo "🚀 Iniciando Rede Social com Django Rest Framework"
echo "=================================================="

# Criar arquivo .env se não existir
if [ ! -f backend/.env ]; then
    echo "📝 Criando arquivo .env..."
    cp backend/.env.example backend/.env
    echo "✅ Arquivo .env criado"
fi

# Iniciar containers
echo "🐳 Iniciando containers Docker..."
docker-compose -f docker/docker-compose.yml up -d

# Aguardar banco de dados
echo "⏳ Aguardando banco de dados..."
sleep 10

# Executar migrações
echo "🔄 Executando migrações..."
docker-compose -f docker/docker-compose.yml exec web python manage.py migrate

# Criar superusuário
echo "👤 Criando superusuário..."
docker-compose -f docker/docker-compose.yml exec web python manage.py createsuperuser --username admin --email admin@example.com --noinput || true

echo ""
echo "✅ Ambiente configurado com sucesso!"
echo "📊 URLs:"
echo "   - API: http://localhost:8000"
echo "   - Admin: http://localhost:8000/admin"
echo "   - Swagger: http://localhost:8000/swagger"
echo "   - Redoc: http://localhost:8000/redoc"
echo "   - MinIO Console: http://localhost:9001"
echo ""
echo "📝 Credenciais padrão:"
echo "   - Admin: admin / admin123"
echo "   - MinIO: minioadmin / minioadmin123"
echo ""
echo "💡 Para parar os containers: docker-compose -f docker/docker-compose.yml down"
echo "🎉 Pronto para começar a desenvolver!"