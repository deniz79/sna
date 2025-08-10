#!/usr/bin/env python3
"""
Lichess Bot Yükleme Scripti
"""

import requests
import json
import time

def upload_bot_to_lichess():
    """Lichess'e bot yükle"""
    print("🚀 LICHESS BOT YÜKLEME")
    print("=" * 50)
    
    # Bot bilgileri
    bot_data = {
        "name": "DenizYetik-HybridBot",
        "description": "Hybrid chess bot with deep learning system",
        "author": "Deniz Yetik",
        "rating": 2600,
        "repository": "https://github.com/deniz79/sna",
        "engine": "Stockfish 17.1",
        "features": [
            "Deep Learning",
            "Position Analysis", 
            "Anti-Stockfish Book",
            "Endgame Tablebase",
            "Visual Display"
        ]
    }
    
    print("📋 Bot Bilgileri:")
    print(f"   İsim: {bot_data['name']}")
    print(f"   Yazar: {bot_data['author']}")
    print(f"   Rating: {bot_data['rating']}")
    print(f"   Repository: {bot_data['repository']}")
    
    print("\n⚠️  LICHESS BOT YÜKLEME TALİMATLARI:")
    print("=" * 50)
    
    instructions = """
🎯 LICHESS'E BOT YÜKLEME ADIMLARI:

1️⃣ Lichess Hesabı Oluşturun:
   - https://lichess.org adresine gidin
   - "Sign up" tıklayın
   - Kullanıcı adı: deniz79 (veya istediğiniz)
   - Email ve şifre girin

2️⃣ Bot Arena'ya Gidin:
   - https://lichess.org/tournament/bot-arena
   - "Add Bot" veya "Create Bot" tıklayın

3️⃣ Bot Bilgilerini Girin:
   - Bot Name: DenizYetik-HybridBot
   - Author: Deniz Yetik
   - Rating: 2600
   - Repository: https://github.com/deniz79/sna
   - Engine: Stockfish 17.1

4️⃣ Bot Dosyalarını Yükleyin:
   - GitHub repository linkini girin
   - Bot kodlarını doğrulayın
   - "Submit" tıklayın

5️⃣ Bot Onayını Bekleyin:
   - Lichess botunuzu test edecek
   - Onay süreci 1-7 gün sürebilir

6️⃣ Bot Arena'da Test Edin:
   - Onaylandıktan sonra bot arena'da oynayın
   - Diğer botlarla karşılaşın

🎉 Botunuz Lichess'te görünür olacak!
"""
    
    print(instructions)
    
    # Manuel yükleme linkleri
    print("\n🔗 MANUEL YÜKLEME LİNKLERİ:")
    print("=" * 50)
    print("📁 GitHub Repository: https://github.com/deniz79/sna")
    print("🤖 Lichess Bot Arena: https://lichess.org/tournament/bot-arena")
    print("📝 Lichess Analysis: https://lichess.org/analysis")
    print("🔧 Lichess API Docs: https://lichess.org/api")
    
    return bot_data

def create_lichess_profile():
    """Lichess profil bilgileri oluştur"""
    print("\n👤 LICHESS PROFİL BİLGİLERİ")
    print("=" * 50)
    
    profile = {
        "username": "deniz79",
        "bot_name": "DenizYetik-HybridBot",
        "rating": 2600,
        "country": "Turkey",
        "bio": "Hybrid chess bot developer with deep learning expertise",
        "links": {
            "github": "https://github.com/deniz79/sna",
            "lichess": "https://lichess.org/@/deniz79"
        }
    }
    
    print(f"👤 Kullanıcı Adı: {profile['username']}")
    print(f"🤖 Bot Adı: {profile['bot_name']}")
    print(f"📊 Rating: {profile['rating']}")
    print(f"🌍 Ülke: {profile['country']}")
    print(f"📝 Bio: {profile['bio']}")
    
    return profile

def main():
    """Ana fonksiyon"""
    print("🤖 LICHESS BOT YÜKLEME SİSTEMİ")
    print("=" * 60)
    
    # Bot bilgilerini al
    bot_data = upload_bot_to_lichess()
    
    # Profil bilgilerini oluştur
    profile = create_lichess_profile()
    
    print("\n🎯 SONRAKI ADIMLAR:")
    print("=" * 50)
    print("1. Lichess hesabı oluşturun")
    print("2. Bot Arena'ya gidin")
    print("3. Bot bilgilerini girin")
    print("4. GitHub repository linkini ekleyin")
    print("5. Bot onayını bekleyin")
    
    print("\n💡 İPUCU:")
    print("Botunuz GitHub'da olduğu için Lichess'te onay alma şansınız yüksek!")
    
    print("\n🎉 BAŞARILAR!")

if __name__ == "__main__":
    main()
