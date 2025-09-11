import os
os.environ['KIVY_NO_CONSOLELOG'] = '1' # Desativa logs do Kivy no console

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

import threading
import time

# Importa a classe do robô do seu arquivo original
from SINALIZADOR_ALPHA_REAL import SinalizadorAlphaReal, EngulfingPatternStrategy, PocketOptionVolumeStrategy, MacdRsiReversalStrategy, HammerPatternStrategy

# Classe para armazenar cores e facilitar o acesso no arquivo .kv
class Colors(ObjectProperty):
    pass

class SinalizadorAlphaApp(App):
    def build(self):
        # Define o objeto de cores para ser acessado globalmente no .kv
        self.colors = Colors()
        Builder.load_file('sinalizador.kv')
        # Inicializa a instância do bot, mas sem a interface gráfica tkinter
        # Passamos um 'update_callback' para que o bot possa nos enviar atualizações
        self.bot_instance = SinalizadorAlphaReal(gui_mode='kivy', update_callback=self.update_ui_callback)
        return Builder.load_file('sinalizador.kv')

    def on_start(self):
        """
        Chamado quando o app inicia. Vamos configurar os valores iniciais da interface.
        """
        self.load_config_to_ui()

    def load_config_to_ui(self):
        """Carrega a configuração do bot para os campos da interface Kivy."""
        config = self.bot_instance.config
        self.root.ids.email_input.text = config.get('email', '')
        self.root.ids.account_type_spinner.text = config.get('account_type', 'PRACTICE')
        self.root.ids.entry_value_input.text = str(config.get('entry_value', '5.0'))
        self.root.ids.stop_win_input.text = str(config.get('stop_win', '100.0'))
        self.root.ids.stop_loss_input.text = str(config.get('stop_loss', '50.0'))
        
        # Preenche o Spinner de estratégias
        strategy_spinner = self.root.ids.strategy_spinner
        strategy_spinner.values = list(self.bot_instance.strategies.keys())
        strategy_spinner.text = config.get('strategy', strategy_spinner.values[0])
        
    def save_real_config(self):
        """Pega os dados da UI e salva no arquivo de configuração."""
        # Pega os valores da interface
        self.bot_instance.config['email'] = self.root.ids.email_input.text
        self.bot_instance.config['password'] = self.root.ids.password_input.text # Pega a senha ao salvar
        self.bot_instance.config['account_type'] = self.root.ids.account_type_spinner.text
        self.bot_instance.config['entry_value'] = float(self.root.ids.entry_value_input.text or '5.0')
        self.bot_instance.config['stop_win'] = float(self.root.ids.stop_win_input.text or '100.0')
        self.bot_instance.config['stop_loss'] = float(self.root.ids.stop_loss_input.text or '50.0')
        self.bot_instance.config['strategy'] = self.root.ids.strategy_spinner.text
        
        # Chama o método de salvar do bot
        self.bot_instance.save_real_config_from_kivy()
        print("Configurações salvas!") # Pode adicionar um Popup de confirmação aqui

    def connect_real_exnova(self):
        """Inicia a conexão em uma thread para não travar a UI."""
        self.root.ids.connect_btn.text = "Conectando..."
        self.root.ids.connect_btn.disabled = True
        
        email = self.root.ids.email_input.text
        password = self.root.ids.password_input.text
        
        thread = threading.Thread(target=self.bot_instance._connect_worker, args=(email, password), daemon=True)
        thread.start()

    def toggle_real_trading(self):
        """Inicia ou para o trading."""
        # A lógica de UI para habilitar/desabilitar botões será controlada pelo callback
        self.bot_instance.toggle_real_trading()

    def update_ui_callback(self, data):
        """
        Este é o método mágico! O bot chama esta função com atualizações.
        Usamos Clock.schedule_once para garantir que a UI seja atualizada na thread principal.
        """
        Clock.schedule_once(lambda dt: self._update_ui(data))

    def _update_ui(self, data):
        """Este método realmente atualiza os widgets da interface."""
        if 'connection_status' in data:
            status = data['connection_status']
            if status == 'success':
                self.root.ids.conexao_label.text = "Conexão: Conectado"
                self.root.ids.conexao_label.color = get_color_from_hex('#10B981') # Verde
                self.root.ids.connect_btn.text = "Conectado"
            else:
                self.root.ids.conexao_label.text = f"Conexão: Falhou"
                self.root.ids.conexao_label.color = get_color_from_hex('#EF4444') # Vermelho
                self.root.ids.connect_btn.text = "🔗 Conectar à Exnova"
                self.root.ids.connect_btn.disabled = False

        if 'trading_status' in data:
            status = data['trading_status']
            self.root.ids.trading_label.text = f"Trading: {status}"
            if "Ativo" in status:
                self.root.ids.trading_btn.text = "⏹️ Parar Trading"
            else:
                self.root.ids.trading_btn.text = "▶️ Iniciar Trading"

        if 'dashboard' in data:
            dash = data['dashboard']
            self.root.ids.saldo_label.text = f"${dash.get('balance', 0):.2f}"
            self.root.ids.lucro_label.text = f"${dash.get('profit', 0):+.2f}"
            self.root.ids.acerto_label.text = f"{dash.get('accuracy', 0):.1f}%"
            self.root.ids.operacoes_label.text = f"{dash.get('wins', 0)}W / {dash.get('losses', 0)}L"
        
        if 'account_type' in data:
            self.root.ids.conta_label.text = f"Conta: {data['account_type']}"

if __name__ == '__main__':
    SinalizadorAlphaApp().run()