#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SINALIZADOR ALPHA - Bot de Trading Profissional
Versão: 5.0 (Estratégias WIN Baseadas em Análise de Vídeos)
Estratégias disponíveis:
1. Pocket Option + Sinais High Volume (82% WIN RATE)
2. Candlestick Psychology - Engulfing Pattern (85% WIN RATE)
3. Hammer & Hanging Man Patterns (75% WIN RATE)
4. MACD + RSI Trend Reversal (80% WIN RATE)
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import time
import json
import os
import sys  # <--- ADICIONADO PARA A CORREÇÃO
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
import ta # Importa a biblioteca de análise técnica

try:
    from exnovaapi.stable_api import Exnova
except ImportError:
    messagebox.showerror("Erro Crítico de Dependência", "A biblioteca da API (exnovaapi) não foi encontrada.\n\nExecute o 'EXECUTAR_BOT.py' e escolha a opção 1 para instalar as dependências.")
    exit()

# --- FUNÇÃO DE CORREÇÃO PARA PYINSTALLER ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto para o recurso, funciona para dev e para o PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# --- FIM DA FUNÇÃO DE CORREÇÃO ---

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('sinalizador_alpha_v5.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TradingStrategyReal:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def is_volatile(self, data: pd.DataFrame) -> bool:
        if self.config.get('enable_volatility_filter', False):
            try:
                atr_period = 14
                if len(data) < atr_period: return False
                atr = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=atr_period)
                last_atr = atr.iloc[-2]
                last_close = data['close'].iloc[-2]
                normalized_atr = (last_atr / last_close) * 100
                
                volatility_threshold = 0.15 
                if normalized_atr > volatility_threshold:
                    logger.warning(f"Análise {self.name}: FILTRO DE VOLATILIDADE ATIVADO. Par ignorado (ATR Normalizado: {normalized_atr:.3f}% > {volatility_threshold}%)")
                    return True
            except Exception as e:
                logger.error(f"Erro no filtro de volatilidade: {e}")
        return False

    def analyze(self, data: pd.DataFrame) -> dict:
        raise NotImplementedError

# --- NOVAS ESTRATÉGIAS IMPLEMENTADAS ---

class PocketOptionVolumeStrategy(TradingStrategyReal):
    def __init__(self, config: dict):
        super().__init__("Pocket Option + Volume (82%)", config)
        self.RSI_PERIOD = 14
        self.VOLUME_AVG_PERIOD = 20
        self.VOLUME_FACTOR = 1.5

    def analyze(self, data: pd.DataFrame) -> dict:
        try:
            if len(data) < max(self.RSI_PERIOD, self.VOLUME_AVG_PERIOD):
                return {"signal": None}

            data[['open', 'high', 'low', 'close', 'volume']] = data[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
            
            rsi = ta.momentum.rsi(data['close'], window=self.RSI_PERIOD)
            volume_avg = data['volume'].rolling(window=self.VOLUME_AVG_PERIOD).mean()
            
            last_candle = data.iloc[-2]
            last_rsi = rsi.iloc[-2]
            last_volume = last_candle['volume']
            last_volume_avg = volume_avg.iloc[-2]

            is_high_volume = last_volume > (last_volume_avg * self.VOLUME_FACTOR)

            if last_rsi < 30 and is_high_volume:
                logger.info(f"Análise {self.name}: Sinal de COMPRA detectado (RSI={last_rsi:.2f}, Volume Alto)")
                return {"signal": "call", "entry_price": last_candle['close'], "assertiveness": 82.0}

            if last_rsi > 70 and is_high_volume:
                logger.info(f"Análise {self.name}: Sinal de VENDA detectado (RSI={last_rsi:.2f}, Volume Alto)")
                return {"signal": "put", "entry_price": last_candle['close'], "assertiveness": 82.0}

            return {"signal": None}
        except Exception as e:
            logger.error(f"Erro na estratégia '{self.name}': {e}")
            return {"signal": None}

class EngulfingPatternStrategy(TradingStrategyReal):
    def __init__(self, config: dict):
        super().__init__("Engulfing Pattern (85%)", config)

    def analyze(self, data: pd.DataFrame) -> dict:
        try:
            if len(data) < 3:
                return {"signal": None}

            data[['open', 'high', 'low', 'close']] = data[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            
            candle_atual = data.iloc[-2]
            candle_anterior = data.iloc[-3]

            # Bullish Engulfing
            is_bullish_engulfing = (candle_anterior['close'] < candle_anterior['open'] and # Anterior é vermelha
                                    candle_atual['close'] > candle_atual['open'] and      # Atual é verde
                                    candle_atual['open'] < candle_anterior['close'] and
                                    candle_atual['close'] > candle_anterior['open'])
            
            if is_bullish_engulfing:
                logger.info(f"Análise {self.name}: Sinal de COMPRA detectado (Bullish Engulfing)")
                return {"signal": "call", "entry_price": candle_atual['close'], "assertiveness": 85.0}

            # Bearish Engulfing
            is_bearish_engulfing = (candle_anterior['close'] > candle_anterior['open'] and # Anterior é verde
                                    candle_atual['close'] < candle_atual['open'] and      # Atual é vermelha
                                    candle_atual['open'] > candle_anterior['close'] and
                                    candle_atual['close'] < candle_anterior['open'])

            if is_bearish_engulfing:
                logger.info(f"Análise {self.name}: Sinal de VENDA detectado (Bearish Engulfing)")
                return {"signal": "put", "entry_price": candle_atual['close'], "assertiveness": 85.0}

            return {"signal": None}
        except Exception as e:
            logger.error(f"Erro na estratégia '{self.name}': {e}")
            return {"signal": None}

class HammerPatternStrategy(TradingStrategyReal):
    def __init__(self, config: dict):
        super().__init__("Hammer & Hanging Man (75%)", config)

    def analyze(self, data: pd.DataFrame) -> dict:
        try:
            if len(data) < 2:
                return {"signal": None}

            data[['open', 'high', 'low', 'close']] = data[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            
            candle = data.iloc[-2]
            
            body_size = abs(candle['close'] - candle['open'])
            if body_size == 0: body_size = 1e-5 # Evita divisão por zero
            
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']

            # Hammer Pattern (Sinal de Compra)
            is_hammer = (lower_shadow > 2 * body_size and upper_shadow < 0.5 * body_size)
            
            if is_hammer:
                logger.info(f"Análise {self.name}: Sinal de COMPRA detectado (Hammer)")
                return {"signal": "call", "entry_price": candle['close'], "assertiveness": 75.0}

            # Hanging Man / Shooting Star Pattern (Sinal de Venda)
            is_hanging_man = (upper_shadow > 2 * body_size and lower_shadow < 0.5 * body_size)
            
            if is_hanging_man:
                logger.info(f"Análise {self.name}: Sinal de VENDA detectado (Hanging Man / Shooting Star)")
                return {"signal": "put", "entry_price": candle['close'], "assertiveness": 75.0}

            return {"signal": None}
        except Exception as e:
            logger.error(f"Erro na estratégia '{self.name}': {e}")
            return {"signal": None}

class MacdRsiReversalStrategy(TradingStrategyReal):
    def __init__(self, config: dict):
        super().__init__("MACD + RSI Reversal (80%)", config)
        self.RSI_PERIOD = 14
        self.MACD_FAST = 12
        self.MACD_SLOW = 26
        self.MACD_SIGN = 9

    def analyze(self, data: pd.DataFrame) -> dict:
        try:
            if len(data) < self.MACD_SLOW:
                return {"signal": None}
            
            data[['open', 'high', 'low', 'close']] = data[['open', 'high', 'low', 'close']].apply(pd.to_numeric)
            
            rsi = ta.momentum.rsi(data['close'], window=self.RSI_PERIOD)
            macd_obj = ta.trend.MACD(close=data['close'], window_fast=self.MACD_FAST, window_slow=self.MACD_SLOW, window_sign=self.MACD_SIGN)
            macd_line = macd_obj.macd()
            signal_line = macd_obj.macd_signal()

            last_rsi = rsi.iloc[-2]
            prev_macd = macd_line.iloc[-3]
            last_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-3]
            last_signal = signal_line.iloc[-2]
            
            candle = data.iloc[-2]

            # Bullish Signal
            macd_crossover_bullish = prev_macd < prev_signal and last_macd > last_signal
            rsi_in_bullish_zone = 25 < last_rsi < 40

            if macd_crossover_bullish and rsi_in_bullish_zone:
                logger.info(f"Análise {self.name}: Sinal de COMPRA detectado (MACD Crossover + RSI={last_rsi:.2f})")
                return {"signal": "call", "entry_price": candle['close'], "assertiveness": 80.0}

            # Bearish Signal
            macd_crossover_bearish = prev_macd > prev_signal and last_macd < last_signal
            rsi_in_bearish_zone = 60 < last_rsi < 75

            if macd_crossover_bearish and rsi_in_bearish_zone:
                logger.info(f"Análise {self.name}: Sinal de VENDA detectado (MACD Crossover + RSI={last_rsi:.2f})")
                return {"signal": "put", "entry_price": candle['close'], "assertiveness": 80.0}

            return {"signal": None}
        except Exception as e:
            logger.error(f"Erro na estratégia '{self.name}': {e}")
            return {"signal": None}

# --- FIM DAS NOVAS ESTRATÉGIAS ---


class SinalizadorAlphaReal:
    def __init__(self):
        self.root = ctk.CTk()
        self.colors = {'bg_main': '#0F172A', 'bg_secondary': '#1E293B', 'card': '#334155', 'primary': '#2563EB', 'green': '#10B981', 'red': '#EF4444', 'yellow': '#F59E0B', 'text_primary': '#F8FAFC', 'text_secondary': '#94A3B8'}
        self.setup_window()
        self.exnova_api = None; self.connected = False; self.trading = False; self.balance = 0.0; self.total_profit = 0.0; self.total_operations = 0; self.total_wins = 0; self.total_losses = 0;
        self.config = {}; self.signals = []
        self.load_real_config() # Carrega config antes de instanciar estratégias
        
        # --- DICIONÁRIO DE ESTRATÉGIAS ATUALIZADO ---
        self.strategies = {
            'Engulfing Pattern (85%)': EngulfingPatternStrategy(self.config),
            'Pocket Option + Volume (82%)': PocketOptionVolumeStrategy(self.config),
            'MACD + RSI Reversal (80%)': MacdRsiReversalStrategy(self.config),
            'Hammer & Hanging Man (75%)': HammerPatternStrategy(self.config)
        }
        # ----------------------------------------------
        
        self.available_otc_pairs = []; self.payouts = {}; self.min_payout = 85
        self.create_real_interface(); self.start_background_thread()

    def setup_window(self):
        self.root.title("🚀 SINALIZADOR ALPHA v5.0 - ESTRATÉGIAS WIN")
        self.root.geometry("1400x900")
        self.root.configure(fg_color=self.colors['bg_main'])
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja fechar o bot?"):
            self.trading = False; time.sleep(1); self.root.destroy()

    def load_real_config(self):
        try:
            # --- CÓDIGO MODIFICADO PARA ENCONTRAR O ARQUIVO NO EXE ---
            config_file_path = resource_path('config_real.json')
            if os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
            # --- FIM DA MODIFICAÇÃO ---
            
            defaults = {
                'email': '', 'password': '', 'account_type': 'PRACTICE',
                'entry_value': 5.0, 'stop_win': 100.0, 'stop_loss': 50.0,
                'strategy': 'Engulfing Pattern (85%)', # <-- Estratégia padrão atualizada
                'operation_mode': 'Operar',
                'optimized_entry': True, 'enable_gap_filter': False,
                'enable_martingale': False,
                'enable_volatility_filter': False
            }
            for k, v in defaults.items(): self.config.setdefault(k, v)
        except Exception as e: logger.error(f"Erro ao carregar config: {e}")

    def save_real_config(self):
        try:
            for key, var in self.ui_vars.items():
                if key != 'strategy': self.config[key] = var.get()
            self.config['strategy'] = self.ui_vars['strategy'].get()
            for key in ['entry_value', 'stop_win', 'stop_loss']:
                try: self.config[key] = float(self.ui_vars[key].get())
                except (ValueError, TypeError): self.config[key] = {'entry_value': 5.0, 'stop_win': 100.0, 'stop_loss': 50.0}[key]
            config_to_save = self.config.copy(); config_to_save.pop('password', None)
            
            # ATENÇÃO: Salvamos sempre no diretório do programa, não no temporário do PyInstaller
            with open('config_real.json', 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4)
                
            messagebox.showinfo("Sucesso", "Configurações salvas!")
            self.root.after(0, self.update_dashboard_ui)
        except Exception as e: messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar as configurações: {e}")

    def create_real_interface(self):
        ctk.CTkLabel(self.root, text="🚀 SINALIZADOR ALPHA", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors['text_primary']).pack(pady=(20, 5))
        ctk.CTkLabel(self.root, text="Bot de Trading Automático para Exnova", font=ctk.CTkFont(size=14), text_color=self.colors['text_secondary']).pack(pady=(0, 20))
        self.tab_view = ctk.CTkTabview(self.root, fg_color=self.colors['bg_secondary']); self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.tab_view.add("📊 Dashboard"); self.tab_view.add("⚙️ Configurações"); self.tab_view.add("📈 Sinais"); self.tab_view.add("💱 Pares de Moedas")
        self.ui_vars = {}
        self.create_dashboard_tab(self.tab_view.tab("📊 Dashboard"))
        self.create_configuracoes_tab(self.tab_view.tab("⚙️ Configurações"))
        self.create_signals_tab(self.tab_view.tab("📈 Sinais"))
        self.create_pairs_tab(self.tab_view.tab("💱 Pares de Moedas"))

    def create_configuracoes_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)
        def create_widget(parent, key, label_text, widget_type, values=None, show=None):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            ctk.CTkLabel(frame, text=label_text, width=200, anchor="w").pack(side="left", padx=(0, 10))
            var = ctk.StringVar() if widget_type != ctk.CTkCheckBox else ctk.BooleanVar()
            var.set(self.config.get(key, ''))
            self.ui_vars[key] = var
            if widget_type == ctk.CTkEntry: widget = ctk.CTkEntry(frame, textvariable=var, width=250, show=show)
            elif widget_type == ctk.CTkOptionMenu: widget = ctk.CTkOptionMenu(frame, variable=var, values=values, width=250)
            elif widget_type == ctk.CTkCheckBox: widget = ctk.CTkCheckBox(frame, text="", variable=var)
            widget.pack(side="left", fill="x", expand=True); return frame
        
        login_card = ctk.CTkFrame(tab, fg_color=self.colors['card']); login_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(login_card, text="Credenciais da Exnova", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        create_widget(login_card, 'email', 'Email:', ctk.CTkEntry).pack(fill="x", padx=20, pady=5)
        create_widget(login_card, 'password', 'Senha:', ctk.CTkEntry, show="*").pack(fill="x", padx=20, pady=5)
        create_widget(login_card, 'account_type', 'Tipo de Conta:', ctk.CTkOptionMenu, values=['PRACTICE', 'REAL']).pack(fill="x", padx=20, pady=(5, 20))
        
        management_card = ctk.CTkFrame(tab, fg_color=self.colors['card']); management_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(management_card, text="Gerenciamento de Risco", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        create_widget(management_card, 'entry_value', 'Valor de Entrada ($):', ctk.CTkEntry).pack(fill="x", padx=20, pady=5)
        create_widget(management_card, 'stop_win', 'Stop Win ($):', ctk.CTkEntry).pack(fill="x", padx=20, pady=5)
        create_widget(management_card, 'stop_loss', 'Stop Loss ($):', ctk.CTkEntry).pack(fill="x", padx=20, pady=(5, 20))
        
        strategy_card = ctk.CTkFrame(tab, fg_color=self.colors['card']); strategy_card.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(strategy_card, text="Configuração de Trading", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        create_widget(strategy_card, 'strategy', 'Estratégia:', ctk.CTkOptionMenu, values=list(self.strategies.keys())).pack(fill="x", padx=20, pady=5)
        create_widget(strategy_card, 'operation_mode', 'Modo de Operação:', ctk.CTkOptionMenu, values=['Operar', 'Analisar']).pack(fill="x", padx=20, pady=5)
        create_widget(strategy_card, 'optimized_entry', 'Otimizar Entrada (Pullback):', ctk.CTkCheckBox).pack(fill="x", padx=20, pady=5)
        create_widget(strategy_card, 'enable_gap_filter', 'Ativar Filtro de GAP:', ctk.CTkCheckBox).pack(fill="x", padx=20, pady=5)
        create_widget(strategy_card, 'enable_martingale', 'Ativar Martingale:', ctk.CTkCheckBox).pack(fill="x", padx=20, pady=5)
        create_widget(strategy_card, 'enable_volatility_filter', 'Ativar Filtro de Volatilidade:', ctk.CTkCheckBox).pack(fill="x", padx=20, pady=(5, 20))
        
        save_button_frame = ctk.CTkFrame(tab, fg_color="transparent"); save_button_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky="s")
        ctk.CTkButton(save_button_frame, text="💾 Salvar Configurações", command=self.save_real_config, height=40).pack()

    def analyze_market_loop(self):
        while True:
            if self.trading:
                strategy = self.strategies.get(self.ui_vars['strategy'].get())
                if not strategy: logger.error(f"Estratégia não encontrada. Parando o loop."); self.root.after(0, self.toggle_real_trading); break
                potential_trades = []
                for pair in self.available_otc_pairs:
                    if not self.trading: break
                    try:
                        candles = self.exnova_api.get_candles(pair, 60, 100, time.time())
                        if not candles or not isinstance(candles, list) or not candles[0] or 'open' not in candles[0]: logger.warning(f"Dados inválidos para {pair}."); continue
                        try: df = pd.DataFrame(candles)
                        except (ValueError, TypeError) as e: logger.error(f"Erro ao criar DataFrame para {pair}: {e}."); continue
                        df.rename(columns={'max': 'high', 'min': 'low', 'from': 'timestamp'}, inplace=True)
                        analysis = strategy.analyze(df)
                        if analysis and analysis.get("signal"): analysis['pair'] = pair; potential_trades.append(analysis)
                    except Exception as e: logger.error(f"Erro ao analisar {pair}: {e}")
                    time.sleep(0.5)
                if self.trading and potential_trades:
                    best_trade = max(potential_trades, key=lambda x: x['assertiveness'])
                    logger.info(f"Sinais encontrados: {len(potential_trades)}. Melhor sinal: {best_trade['pair']} com {best_trade['assertiveness']}% de assertividade.")
                    threading.Thread(target=self._process_trade_thread, args=(best_trade['pair'], best_trade), daemon=True).start()
                    time.sleep(60)
                else: time.sleep(5)
            else: time.sleep(5)

    def _process_trade_thread(self, pair, signal_data):
        try:
            wait_time = max(0, 60 - datetime.now().second)
            logger.info(f"Sinal de {signal_data['signal'].upper()} para {pair}. Aguardando {wait_time:.1f}s para a próxima vela.")
            time.sleep(wait_time)
            if self.config['operation_mode'] == 'Operar':
                if self.payouts.get(pair, 0) < self.min_payout: logger.warning(f"TRADE CANCELADO ({pair}): Payout baixo."); return
                if self.total_profit >= self.config['stop_win']: logger.warning("TRADE CANCELADO: Meta Stop Win atingida."); self.root.after(0, self.toggle_real_trading); return
                if self.total_profit < 0 and abs(self.total_profit) >= self.config['stop_loss']: logger.warning("TRADE CANCELADO: Limite Stop Loss atingido."); self.root.after(0, self.toggle_real_trading); return
            self._send_trade(pair, signal_data)
        except Exception as e: logger.error(f"Erro CRÍTICO no processamento do trade para {pair}: {e}", exc_info=True)

    def _send_trade(self, pair, signal_data, is_martingale=False):
        amount = signal_data.get('amount', self.config['entry_value'])
        direction = signal_data['signal']
        assertiveness = signal_data.get('assertiveness', 'GALE')

        strategy_name = f"{self.config.get('strategy')} (GALE)" if is_martingale else self.config.get('strategy')
        
        signal = {'id': time.time(), 'pair': pair, 'direction': direction, 'status': 'AGUARDANDO', 'profit': 0, 'entry_time': datetime.now(), 'exit_time': datetime.now(), 'amount': amount, 'strategy': strategy_name, 'assertiveness': assertiveness}
        self.signals.append(signal)

        if self.config.get('enable_gap_filter', False) and not is_martingale:
            try:
                candles = self.exnova_api.get_candles(pair, 60, 2, time.time())
                if candles and len(candles) == 2 and candles[0]['open'] != candles[1]['close']:
                    logger.warning(f"TRADE CANCELADO ({pair}): GAP DETECTADO.")
                    signal['status'] = 'CANCELADO (GAP)'; self.root.after(0, self.update_signals_ui); return
            except Exception as e: logger.error(f"Erro ao verificar GAP para {pair}: {e}")

        current_price, _ = self._get_current_price(pair)
        if not current_price: 
            logger.error(f"Não foi possível obter preço para {pair}."); signal['status'] = 'ERRO (PREÇO)'; return
        signal['entry_price'] = current_price
        self.root.after(0, self.update_signals_ui)

        is_catalog = self.config['operation_mode'] == 'Analisar'
        if not is_catalog:
            log_msg = f"Enviando ordem de MARTINGALE:" if is_martingale else "Enviando ordem REAL:"
            logger.info(f"{log_msg} {direction.upper()} em {pair} | Valor ${amount}")
            status, order_id = self.exnova_api.buy(amount, pair, direction, 1)
            if status: 
                logger.info(f"Ordem {order_id} enviada."); self.total_operations += 1
                self.root.after(65000, lambda: self.check_trade_result(order_id, amount, signal['id']))
            else: 
                logger.error(f"Falha ao enviar ordem para {pair}. API: {order_id}"); signal['status'] = 'ERRO'
                self.root.after(0, self.update_signals_ui)
        else:
            self.total_operations += 1
            self.root.after(65000, lambda: self.check_trade_result(None, amount, signal['id'], is_catalog=True, pair=pair, entry_price=signal['entry_price'], direction=direction))

    def create_dashboard_tab(self, tab):
        tab.grid_columnconfigure(0, weight=3); tab.grid_columnconfigure(1, weight=1); tab.grid_rowconfigure(1, weight=1)
        metrics_frame = ctk.CTkFrame(tab, fg_color="transparent"); metrics_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10); metrics_frame.grid_columnconfigure((0,1,2,3), weight=1)
        self.saldo_label = self._create_metric_card(metrics_frame, 0, "SALDO", "$0.00", self.colors['green'])
        self.lucro_label = self._create_metric_card(metrics_frame, 1, "LUCRO TOTAL", "$+0.00", self.colors['primary'])
        self.acerto_label = self._create_metric_card(metrics_frame, 2, "TAXA DE ACERTO", "0.0%", self.colors['yellow'])
        self.operacoes_label = self._create_metric_card(metrics_frame, 3, "OPERAÇÕES", "0W / 0L", self.colors['text_primary'])
        status_card = ctk.CTkFrame(tab, fg_color=self.colors['card']); status_card.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(status_card, text="Status do Bot", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.conexao_label = ctk.CTkLabel(status_card, text="Conexão: Desconectado", anchor="w", text_color=self.colors['red']); self.conexao_label.pack(fill="x", padx=20, pady=2)
        self.trading_label = ctk.CTkLabel(status_card, text="Trading: Parado", anchor="w", text_color=self.colors['text_secondary']); self.trading_label.pack(fill="x", padx=20, pady=2)
        self.conta_label = ctk.CTkLabel(status_card, text="Conta: -", anchor="w"); self.conta_label.pack(fill="x", padx=20, pady=2)
        self.controls_frame = ctk.CTkFrame(status_card, fg_color="transparent"); self.controls_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        self.connect_btn = ctk.CTkButton(self.controls_frame, text="🔗 Conectar à Exnova", height=40, command=self.connect_real_exnova); self.connect_btn.pack(fill="x", expand=True)
        self.trading_btn = ctk.CTkButton(self.controls_frame, text="▶️ Iniciar Trading", height=40, command=self.toggle_real_trading, fg_color=self.colors['green'])
        self.parar_trading_btn = ctk.CTkButton(self.controls_frame, text="⏹️ Parar Trading", height=40, command=self.toggle_real_trading, fg_color=self.colors['red'])
        metas_card = ctk.CTkFrame(tab, fg_color=self.colors['card']); metas_card.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(metas_card, text="Metas e Limites", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 20))
        self.stop_win_progress = self._create_progress_bar(metas_card, "Stop WIN", f"${self.config.get('stop_win', 100)}", self.colors['green'])
        self.stop_loss_progress = self._create_progress_bar(metas_card, "Stop LOSS", f"${self.config.get('stop_loss', 50)}", self.colors['red'])

    def _create_metric_card(self, parent, col, title, initial_value, color):
        card = ctk.CTkFrame(parent, fg_color=self.colors['card']); card.grid(row=0, column=col, sticky="ew", padx=5)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12), text_color=self.colors['text_secondary']).pack(pady=(10,0))
        label = ctk.CTkLabel(card, text=initial_value, font=ctk.CTkFont(size=24, weight="bold"), text_color=color); label.pack(pady=(0, 10)); return label

    def _create_progress_bar(self, parent, title, value, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent"); frame.pack(fill="x", padx=20, pady=10)
        top_frame = ctk.CTkFrame(frame, fg_color="transparent"); top_frame.pack(fill="x")
        ctk.CTkLabel(top_frame, text=title, text_color=self.colors['text_secondary']).pack(side="left"); ctk.CTkLabel(top_frame, text=value, text_color=self.colors['text_primary']).pack(side="right")
        progress_bar = ctk.CTkProgressBar(frame, progress_color=color); progress_bar.set(0); progress_bar.pack(fill="x", pady=(5,0)); return progress_bar

    def update_dashboard_ui(self):
        self.saldo_label.configure(text=f"${self.balance:.2f}"); self.lucro_label.configure(text=f"${self.total_profit:+.2f}")
        accuracy = (self.total_wins / self.total_operations * 100) if self.total_operations > 0 else 0
        self.acerto_label.configure(text=f"{accuracy:.1f}%"); self.operacoes_label.configure(text=f"{self.total_wins}W / {self.total_losses}L")
        stop_win_value = self.config.get('stop_win', 100.0); stop_loss_value = self.config.get('stop_loss', 50.0)
        for widget in self.stop_win_progress.master.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children():
                    if isinstance(sub_widget, ctk.CTkLabel) and sub_widget.cget('text').startswith('$'): sub_widget.configure(text=f"${stop_win_value:.2f}")
        for widget in self.stop_loss_progress.master.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for sub_widget in widget.winfo_children():
                    if isinstance(sub_widget, ctk.CTkLabel) and sub_widget.cget('text').startswith('$'): sub_widget.configure(text=f"${stop_loss_value:.2f}")
        win_progress = (self.total_profit / stop_win_value) if stop_win_value > 0 else 0; self.stop_win_progress.set(min(1, max(0, win_progress)))
        loss_value = abs(self.total_profit) if self.total_profit < 0 else 0
        loss_progress = (loss_value / stop_loss_value) if stop_loss_value > 0 else 0; self.stop_loss_progress.set(min(1, max(0, loss_progress)))

    def create_signals_tab(self, tab):
        ctk.CTkLabel(tab, text="Sinais de Trading", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 0)); ctk.CTkLabel(tab, text="Últimos sinais gerados pelo bot", font=ctk.CTkFont(size=14), text_color=self.colors['text_secondary']).pack(pady=(0, 20))
        self.signals_scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent"); self.signals_scroll_frame.pack(fill="both", expand=True, padx=10)

    def update_signals_ui(self):
        for widget in self.signals_scroll_frame.winfo_children(): widget.destroy()
        if not self.signals: ctk.CTkLabel(self.signals_scroll_frame, text="Aguardando novos sinais...", font=ctk.CTkFont(size=16), text_color=self.colors['text_secondary']).pack(expand=True, padx=20, pady=20); return
        for signal in reversed(self.signals[-50:]):
            card = ctk.CTkFrame(self.signals_scroll_frame, fg_color=self.colors['card'], corner_radius=10); card.pack(fill="x", pady=8, padx=5)
            header_frame = ctk.CTkFrame(card, fg_color="transparent"); header_frame.pack(fill="x", padx=15, pady=(10, 5)); header_frame.grid_columnconfigure((0,1), weight=1)
            pair_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent"); pair_info_frame.grid(row=0, column=0, sticky="w")
            direction_icon = "📈" if signal['direction'] == 'call' else "📉"
            ctk.CTkLabel(pair_info_frame, text=direction_icon, font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 5)); ctk.CTkLabel(pair_info_frame, text=signal['pair'], font=ctk.CTkFont(size=18, weight="bold")).pack(side="left"); ctk.CTkLabel(pair_info_frame, text=signal['entry_time'].strftime('%d/%m/%Y, %H:%M:%S'), font=ctk.CTkFont(size=12), text_color=self.colors['text_secondary']).pack(side="left", padx=10)
            status = signal.get('status', 'AGUARDANDO'); status_color = self.colors['green'] if status == 'WIN' else self.colors['red'] if status == 'LOSS' else "#64748B"; status_text = status.upper()
            status_badge_frame = ctk.CTkFrame(header_frame, fg_color="transparent"); status_badge_frame.grid(row=0, column=1, sticky="e")
            status_badge = ctk.CTkFrame(status_badge_frame, fg_color=status_color, corner_radius=5); status_badge.pack(); ctk.CTkLabel(status_badge, text=status_text, font=ctk.CTkFont(size=12, weight="bold"), text_color="#FFFFFF").pack(padx=10, pady=3)
            ctk.CTkFrame(card, height=1, fg_color=self.colors['bg_secondary']).pack(fill="x", padx=15, pady=5)
            body_frame = ctk.CTkFrame(card, fg_color="transparent"); body_frame.pack(fill="x", expand=True, padx=15, pady=5)
            def create_info_item(parent, text_title, text_value):
                item_frame = ctk.CTkFrame(parent, fg_color="transparent"); ctk.CTkLabel(item_frame, text=text_title, font=ctk.CTkFont(size=12), text_color=self.colors['text_secondary']).pack(side="left", padx=(0, 5)); ctk.CTkLabel(item_frame, text=text_value, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left"); return item_frame
            create_info_item(body_frame, "Direção:", signal['direction'].upper()).pack(side="left", expand=True, anchor="w")
            assertiveness = signal.get('assertiveness')
            assertiveness_value = f"{assertiveness}%" if isinstance(assertiveness, (int, float)) else assertiveness
            create_info_item(body_frame, "Assertividade:", assertiveness_value).pack(side="left", expand=True, anchor="w")
            entry_price_text = f"${signal.get('entry_price', 0.0):.5f}" if signal.get('entry_price') else "N/A"
            create_info_item(body_frame, "Entrada:", entry_price_text).pack(side="left", expand=True, anchor="w"); create_info_item(body_frame, "Valor:", f"${signal.get('amount', 0.0):.2f}").pack(side="left", expand=True, anchor="w")
            if status in ['WIN', 'LOSS']:
                result_frame = ctk.CTkFrame(card, fg_color="transparent"); result_frame.pack(fill="x", padx=15, pady=(0, 10)); result_frame.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(result_frame, text="Resultado:", font=ctk.CTkFont(size=14)).grid(row=0, column=0, sticky="w")
                profit_color = self.colors['green'] if status == 'WIN' else self.colors['red']; profit_text = f"+${signal['profit']:.2f}" if status == 'WIN' else f"${signal['profit']:.2f}"
                ctk.CTkLabel(result_frame, text=profit_text, font=ctk.CTkFont(size=16, weight="bold"), text_color=profit_color).grid(row=0, column=1, sticky="e")

    def create_pairs_tab(self, tab):
        ctk.CTkLabel(tab, text="Pares de Moedas OTC", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.pairs_scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent"); self.pairs_scroll_frame.pack(fill="both", expand=True, padx=10)

    def update_pairs_ui(self):
        for widget in self.pairs_scroll_frame.winfo_children(): widget.destroy()
        self.pairs_scroll_frame.grid_columnconfigure(tuple(range(4)), weight=1); row, col = 0, 0
        sorted_pairs = sorted(self.available_otc_pairs, key=lambda p: self.payouts.get(p, 0), reverse=True)
        for pair in sorted_pairs:
            card = ctk.CTkFrame(self.pairs_scroll_frame, fg_color=self.colors['card']); card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5); card.grid_columnconfigure((0,1), weight=1)
            payout = self.payouts.get(pair, 0); payout_color = self.colors['green'] if payout >= self.min_payout else self.colors['yellow'] if payout > 0 else self.colors['red']
            ctk.CTkLabel(card, text=pair, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10); ctk.CTkLabel(card, text=f"{payout}%", text_color=payout_color, font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=10, pady=(0,10))
            col += 1;
            if col > 3: col = 0; row += 1

    def update_pairs_ui_with_message(self, message):
        for widget in self.pairs_scroll_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.pairs_scroll_frame, text=message, font=ctk.CTkFont(size=16), text_color=self.colors['text_secondary'], wraplength=500).pack(expand=True, padx=20, pady=20)

    def connect_real_exnova(self):
        email = self.ui_vars['email'].get().strip(); password = self.ui_vars['password'].get()
        if not email or not password: messagebox.showerror("Erro", "Preencha email e senha."); return
        self.connect_btn.configure(text="Conectando...", state="disabled"); threading.Thread(target=self._connect_worker, args=(email, password), daemon=True).start()

    def _connect_worker(self, email, password):
        try:
            self.exnova_api = Exnova(email, password); status, reason = self.exnova_api.connect()
            if status: self.root.after(0, self.update_connection_success)
            else: self.root.after(0, lambda: self.update_connection_failed(reason))
        except Exception as e: logger.error(f"Exceção na conexão: {e}"); self.root.after(0, lambda: self.update_connection_failed(str(e)))

    def _update_asset_data(self):
        try:
            logger.info("Iniciando a busca por pares de moedas OTC..."); all_assets = self.exnova_api.get_all_init_v2(); temp_pairs = []; temp_payouts = {}
            if not all_assets: logger.warning("API get_all_init_v2() retornou vazio."); self.root.after(0, lambda: self.update_pairs_ui_with_message("Não foi possível carregar os pares (resposta vazia da API).")); return
            for asset_type in ['binary', 'turbo']:
                if asset_type in all_assets and 'actives' in all_assets[asset_type] and all_assets[asset_type]['actives']:
                    for asset_data in all_assets[asset_type]['actives'].values():
                        if isinstance(asset_data, dict) and asset_data.get('enabled') and not asset_data.get('is_suspended'):
                            name = asset_data.get('name', '').removeprefix('front.')
                            if 'OTC' in name:
                                if name not in temp_pairs: temp_pairs.append(name)
                                payout = 100 - asset_data.get('option', {}).get('profit', {}).get('commission', 100); temp_payouts[name] = int(payout)
            self.available_otc_pairs = sorted(temp_pairs); self.payouts = temp_payouts
            if not self.available_otc_pairs: logger.warning("Nenhum par OTC aberto."); self.root.after(0, lambda: self.update_pairs_ui_with_message("Nenhum par OTC encontrado aberto no momento."))
            else: logger.info(f"Encontrados {len(self.available_otc_pairs)} pares OTC."); self.root.after(0, self.update_pairs_ui)
        except Exception as e: logger.error(f"Erro CRÍTICO ao atualizar ativos: {e}", exc_info=True); self.root.after(0, lambda: self.update_pairs_ui_with_message(f"Erro ao carregar pares. Verifique o log."))

    def update_connection_success(self):
        self.connected = True; self.connect_btn.pack_forget(); self.trading_btn.pack(fill="x", expand=True)
        self.conexao_label.configure(text=f"Conexão: Conectado", text_color=self.colors['green'])
        account_type = self.ui_vars['account_type'].get(); self.exnova_api.change_balance(account_type)
        self.balance = self.exnova_api.get_balance(); self.conta_label.configure(text=f"Conta: {account_type}")
        self.update_dashboard_ui(); messagebox.showinfo("Sucesso", f"Conectado!\nSaldo: ${self.balance:.2f}")
        threading.Thread(target=self._update_asset_data, daemon=True).start()

    def update_connection_failed(self, reason):
        self.connected = False; self.connect_btn.configure(text="🔗 Conectar", state="normal"); self.conexao_label.configure(text="Conexão: Desconectado", text_color=self.colors['red'])
        messagebox.showerror("Erro de Conexão", f"Falha ao conectar: {reason or 'Verifique suas credenciais.'}")

    def toggle_real_trading(self):
        if not self.connected: messagebox.showerror("Erro", "Conecte-se primeiro!"); return
        if not self.available_otc_pairs: messagebox.showwarning("Aviso", "Nenhum par de moeda foi carregado. Não é possível iniciar."); return
        self.trading = not self.trading
        if self.trading: self.save_real_config(); self.trading_btn.pack_forget(); self.parar_trading_btn.pack(fill="x", expand=True); self.trading_label.configure(text=f"Trading: Ativo ({self.config['operation_mode']})", text_color=self.colors['green'])
        else: self.parar_trading_btn.pack_forget(); self.trading_btn.pack(fill="x", expand=True); self.trading_label.configure(text="Trading: Parado", text_color=self.colors['text_secondary'])

    def _get_current_price(self, pair):
        try:
            candles = self.exnova_api.get_candles(pair, 60, 1, time.time())
            if candles: return candles[0]['close'], candles[0]['open']
        except Exception as e: logger.error(f"Falha ao obter preço atual para {pair}: {e}")
        return None, None
    
    def check_trade_result(self, order_id, amount, signal_id, is_catalog=False, **kwargs):
        try:
            signal = next((s for s in self.signals if s['id'] == signal_id), None)
            if not signal: return
            
            win_amount = 0
            if not is_catalog:
                result = self.exnova_api.check_win_v4(order_id)
                if isinstance(result, (tuple, list)) and len(result) > 0:
                    numeric_results = [val for val in result if isinstance(val, (int, float))]; win_amount = numeric_results[0] if numeric_results else 0
                elif isinstance(result, (int, float)): win_amount = result
            else: # Lógica para modo 'Analisar'
                final_price_candles = self.exnova_api.get_candles(kwargs['pair'], 60, 1, time.time())
                if final_price_candles:
                    final_price = final_price_candles[0]['close']; entry_price = kwargs['entry_price']; direction = kwargs['direction']
                    if (direction == 'call' and final_price > entry_price) or (direction == 'put' and final_price < entry_price):
                        payout_percent = self.payouts.get(kwargs['pair'], self.min_payout) / 100.0; win_amount = amount * payout_percent
            
            signal['exit_time'] = datetime.now()
            if win_amount > 0: # WIN
                profit = win_amount if not is_catalog else (amount * (self.payouts.get(signal['pair'], self.min_payout) / 100.0))
                if not is_catalog: self.total_profit += profit
                self.total_wins += 1; signal['status'] = 'WIN'; signal['profit'] = profit
            else: # LOSS
                if not is_catalog: self.total_profit -= amount
                self.total_losses += 1; signal['status'] = 'LOSS'; signal['profit'] = -amount
                
                if self.config.get('enable_martingale', False) and self.config['operation_mode'] == 'Operar':
                    logger.info(f"LOSS. Acionando Martingale para {signal['pair']}.")
                    new_amount = amount * 2
                    martingale_data = {'signal': signal['direction'], 'pair': signal['pair'], 'amount': new_amount}
                    threading.Thread(target=self._execute_martingale_trade, args=(martingale_data,)).start()

            if not is_catalog: self.balance = self.exnova_api.get_balance()
            logger.info(f"Resultado {signal['id']}: {signal['status']} | Lucro: ${signal['profit']:.2f} | Saldo Atual: ${self.balance:.2f}")
            self.root.after(0, self.update_dashboard_ui); self.root.after(0, self.update_signals_ui)
        except Exception as e: logger.error(f"Erro CRÍTICO ao verificar resultado do trade {order_id}: {e}", exc_info=True)

    def _execute_martingale_trade(self, trade_data):
        try:
            pair = trade_data['pair']
            logger.info(f"Verificando condições para a entrada de Martingale em {pair}...")
            time.sleep(1) 

            if not self.trading:
                logger.warning(f"MARTINGALE CANCELADO ({pair}): O trading foi parado.")
                return

            if self.payouts.get(pair, 0) < self.min_payout:
                logger.warning(f"MARTINGALE CANCELADO ({pair}): Payout baixo ({self.payouts.get(pair, 0)}%).")
                return

            if self.total_profit >= self.config.get('stop_win', float('inf')):
                logger.warning(f"MARTINGALE CANCELADO ({pair}): Meta Stop Win atingida.")
                self.root.after(0, self.toggle_real_trading)
                return

            if self.total_profit < 0 and abs(self.total_profit) >= self.config.get('stop_loss', float('inf')):
                logger.warning(f"MARTINGALE CANCELADO ({pair}): Limite Stop Loss atingido.")
                self.root.after(0, self.toggle_real_trading)
                return
            
            self._send_trade(pair, trade_data, is_martingale=True)
        except Exception as e:
            logger.error(f"Erro CRÍTICO ao executar o Martingale para {trade_data.get('pair')}: {e}", exc_info=True)

    def start_background_thread(self):
        threading.Thread(target=self.analyze_market_loop, daemon=True).start()
        def asset_updater_loop():
            while True:
                time.sleep(1800)
                if self.connected: self._update_asset_data()
        threading.Thread(target=asset_updater_loop, daemon=True).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SinalizadorAlphaReal()
    app.run()