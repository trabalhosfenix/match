#!/bin/bash

echo "🧪 Executando testes da Rede Social DRF"
echo "========================================"

# Executar testes com cobertura
pytest \
  --cov=apps \
  --cov-report=html \
  --cov-report=term \
  --cov-report=xml \
  --ds=config.settings \
  -v \
  --strict-markers

# Exibir resultado
if [ $? -eq 0 ]; then
    echo "✅ Todos os testes passaram!"
    echo "📊 Relatório HTML: htmlcov/index.html"
else
    echo "❌ Alguns testes falharam"
fi