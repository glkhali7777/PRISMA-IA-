#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 EXECUTAR BOT - SINALIZADOR ALPHA
Script principal para executar o bot de forma simplificada
Versão: 3.3 (Com instalador robusto)
"""

import os
import sys
import subprocess
import time

def verificar_python():
    """Verificar se Python 3.8+ está instalado."""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ ERRO: Python 3.8 ou superior é necessário para rodar o bot.")
            print(f"   Sua versão atual é: {version.major}.{version.minor}")
            return False
        print(f"✅ Versão do Python ({version.major}.{version.minor}) verificada.")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar a versão do Python: {e}")
        return False

def instalar_dependencias():
    """
    Função corrigida para instalar dependências de forma mais robusta.
    Inclui instalação direta da ExnovaAPI do CassDs.
    """
    print("\n📦 Verificando e instalando dependências...")

    # Passo 1: Verificar se o Git está instalado, pois é necessário para o método alternativo.
    try:
        subprocess.check_call(['git', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✅ Git encontrado no sistema.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n============================== ATENÇÃO ==============================")
        print("❌ O programa 'Git' não foi encontrado no seu sistema.")
        print("   Ele é essencial para instalar a API da corretora caso o método padrão falhe.")
        print("\n   Por favor, baixe e instale o Git a partir deste site:")
        print("   >>> https://git-scm.com/downloads <<<")
        print("\n   Durante a instalação, pode deixar todas as opções padrão.")
        print("=====================================================================")
        input("\nPressione ENTER para continuar mesmo assim...")

    # Passo 2: Instalar ExnovaAPI do CassDs SEMPRE, por segurança.
    print("\n--- Instalando ExnovaAPI do CassDs ---")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://github.com/CassDs/exnovaapi.git"])
        print("✅ ExnovaAPI instalada com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao instalar ExnovaAPI: {e}")

    # Passo 3: Tentar instalar as dependências do arquivo 'requirements_real.txt'.
    requirements_file = "requirements_real.txt"
    if not os.path.exists(requirements_file):
        print(f"❌ Arquivo '{requirements_file}' não encontrado. Certifique-se que ele está na mesma pasta.")
        return False

    try:
        print(f"\n--- Instalando dependências de '{requirements_file}' ---")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("\n✅ Todas as dependências foram instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("\n⚠️ A instalação padrão falhou. O pacote da API não foi encontrado.")
        return False

def executar_bot_desktop():
    """Executar a versão desktop do bot."""
    print("\n🖥️  Iniciando o SINALIZADOR ALPHA...")
    
    main_script = "SINALIZADOR_ALPHA_REAL.py"
    if not os.path.exists(main_script):
        print(f"❌ Arquivo principal '{main_script}' não foi encontrado!")
        print("   Verifique se você renomeou ou removeu o arquivo da pasta.")
        return

    try:
        subprocess.run([sys.executable, main_script])
    except Exception as e:
        print(f"❌ Erro ao executar o bot: {e}")

def main():
    """Função principal do menu."""
    print("=" * 60)
    print("        🚀 BEM-VINDO AO SINALIZADOR ALPHA v3.3 🚀")
    print("=" * 60)

    if not verificar_python():
        input("\nPressione ENTER para sair...")
        return

    while True:
        print("\nMENU PRINCIPAL:")
        print("1. Instalar/Atualizar Dependências")
        print("2. Executar Bot")
        print("3. Sair")
        
        escolha = input("Digite sua escolha (1-3): ").strip()
        
        if escolha == '1':
            instalar_dependencias()
        elif escolha == '2':
            executar_bot_desktop()
            break 
        elif escolha == '3':
            print("\n👋 Obrigado por usar o SINALIZADOR ALPHA! Bons trades!")
            break
        else:
            print("❌ Opção inválida. Por favor, tente novamente.")
        
        input("\nPressione ENTER para continuar...")

if __name__ == "__main__":
    main()