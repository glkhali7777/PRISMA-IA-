#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 SINALIZADOR ALPHA - Servidor Web Futurista
Versão: 5.5 (Corrigido para nova assinatura do método analyze)
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime, timedelta
import webbrowser
from SINALIZADOR_ALPHA_REAL import SinalizadorAlphaReal
import pandas as pd
import json
import os
import logging

# Configuração de logging para o servidor web
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('sinalizador_alpha_web.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte'
socketio = SocketIO(app, async_mode='threading')

bot_instance = None
last_signals = {}
signal_history = []
config = {}
CONFIG_FILE = 'config_real.json'

def load_config():
    """Carrega as configurações do arquivo JSON."""
    global config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        logger.warning(f"Arquivo de configuração '{CONFIG_FILE}' não encontrado. Usando padrões.")
        config = {
            'email': '', 'password': '', 'account_type': 'PRACTICE',
            'entry_value': 5.0, 'stop_win': 100.0, 'stop_loss': 50.0,
            'strategy': 'Estratégia de GAP',
            'operation_mode': 'Analisar', 'optimized_entry': False
        }

def initialize_bot():
    """Inicializa a instância do bot sem a interface gráfica."""
    global bot_instance
    if not bot_instance:
        logger.info("Criando instância do Sinalizador Alpha para o servidor web...")
        bot_instance = SinalizadorAlphaReal()
        
        # Conectar à Exnova em segundo plano
        if bot_instance.config.get('email') and bot_instance.config.get('password'):
            logger.info("Conectando à Exnova em segundo plano...")
            threading.Thread(
                target=bot_instance._connect_worker, 
                args=(bot_instance.config['email'], bot_instance.config['password']), 
                daemon=True
            ).start()
        
        # Iniciar o loop de análise do mercado
        threading.Thread(target=analyze_market_loop, daemon=True).start()

def analyze_market_loop():
    """Loop de análise de mercado para o servidor web."""
    while True:
        if bot_instance and bot_instance.connected and bot_instance.available_otc_pairs:
            selected_strategy_name = bot_instance.config.get('strategy')
            strategy_instance = bot_instance.strategies.get(selected_strategy_name)

            if not strategy_instance:
                logger.error(f"Estratégia '{selected_strategy_name}' não encontrada. Verifique o arquivo config_real.json.")
                time.sleep(60)
                continue

            found_signals = []
            
            for pair in bot_instance.available_otc_pairs:
                try:
                    candles = bot_instance.exnova_api.get_candles(pair, 60, 30, time.time())
                    if candles and len(candles) >= 20:
                        df = pd.DataFrame(candles)
                        df.rename(columns={'max': 'high', 'min': 'low'}, inplace=True)
                        
                        # CORREÇÃO CRÍTICA: Passar o 'pair' para a função analyze
                        analysis = strategy_instance.analyze(df, pair)
                        
                        if analysis.get("signal"):
                            entry_time = (datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1)).strftime('%H:%M')
                            signal_id = f"{pair}-{entry_time}"
                            
                            # Evita emitir o mesmo sinal repetidamente
                            if last_signals.get(pair) != signal_id:
                                signal = {
                                    "pair": pair,
                                    "time": entry_time,
                                    "direction": analysis["signal"].upper(),
                                    "assertiveness": f'{analysis["assertiveness"]:.2f}%'
                                }
                                found_signals.append(signal)
                                signal_history.append(signal)
                                last_signals[pair] = signal_id
                                
                except Exception as e:
                    logger.error(f"Erro ao analisar {pair}: {e}", exc_info=True)
            
            if found_signals:
                socketio.emit('new_signals', found_signals)
            else:
                socketio.emit('no_signal', {'message': 'Nenhum sinal de alta assertividade encontrado.'})
                
        else:
            logger.info("Aguardando conexão com a Exnova e carregamento de pares...")
        
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    logger.info("Cliente conectado ao servidor web.")
    emit('status', {'message': 'Conectado ao servidor web.'})
    emit('signal_history', signal_history)

def run_web_server():
    load_config()
    initialize_bot()
    logger.info("Servidor web iniciado em http://127.0.0.1:5000")
    webbrowser.open("http://127.0.0.1:5000")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    run_web_server()