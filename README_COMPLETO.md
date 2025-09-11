# 🚀 SINALIZADOR ALPHA v4.0 - Edição Análise de Candle

**Bot de Trading Profissional para Exnova com Análise de Força de Candle**

## 📊 **O que é o SINALIZADOR ALPHA?**

O SINALIZADOR ALPHA é um robô que executa operações automaticamente na corretora **Exnova**. Esta versão foi totalmente redesenhada para focar em uma única e poderosa estratégia: a análise de candles "ativos" e "inativos", que busca identificar a verdadeira força do mercado a cada momento.

- ✅ **Operações REAIS** na Exnova
- ✅ **Estratégia Avançada** de Análise de Candle
- ✅ **WhatsApp Real** para notificações
- ✅ **Interface Profissional** e intuitiva
- ✅ **Multi-Plataforma**: Desktop, Web e Executável

---

## 🎯 **Estratégia Implementada: Candlestick Ativo e Inativo**

### Lógica da Estratégia
A estratégia se baseia na premissa de que cada candle representa uma batalha entre compradores e vendedores. A força "ativa" é a que domina o movimento, enquanto a força "inativa" representa a pressão que foi rejeitada.

- **Análise de Força**: O robô calcula a proporção entre o tamanho do **corpo** da vela (força de momento) e a soma de seus **pavios/sombras** (força de rejeição/indecisão).
- **Candle Ativo (Sinal Forte)**: Um candle é considerado "ativo" quando seu corpo é significativamente maior que seus pavios. Isso indica que a força (compradora ou vendedora) que define a cor da vela está no controle.
- **Candle Inativo (Sem Sinal)**: Velas com corpos pequenos e pavios longos (como Dojis) são consideradas "inativas" e indicam indecisão no mercado. O robô ignora esses candles para evitar entradas de baixo potencial.

### Gatilhos de Entrada
- **Sinal de Compra (CALL)**: Ocorre após uma vela de alta (verde) ser identificada como "ativa", mostrando forte pressão compradora. A entrada é feita no início da vela seguinte.
- **Sinal de Venda (PUT)**: Ocorre após uma vela de baixa (vermelha) ser identificada como "ativa", mostrando forte pressão vendedora. A entrada é feita no início da vela seguinte.

> **Disclaimer**: A precisão desta estratégia é variável e depende das condições do mercado. **SEMPRE** teste em sua conta DEMO antes de operar em conta real para entender seu funcionamento.

---

## 📦 **Como Baixar e Instalar**

### **Opção 1: Executar com Python** ⚡
```bash
# 1. Baixe todos os arquivos para uma pasta
# 2. Abra o terminal (PowerShell/CMD) nessa pasta
# 3. Execute:
python EXECUTAR_BOT.py

# Ou, se o comando acima não funcionar:
python3 EXECUTAR_BOT.py