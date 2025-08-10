#!/usr/bin/env python3
"""
Lichess Bot API Kurulum Sistemi
"""

import requests
import json
import time
from pathlib import Path

class LichessBotAPI:
    """Lichess Bot API sistemi"""
    
    def __init__(self):
        self.api_base = "https://lichess.org/api"
        self.bot_username = "deniz79_bot"  # Bot kullanıcı adı
        self.bot_name = "DenizYetik-HybridBot"
        self.github_repo = "https://github.com/deniz79/sna"
        
    def create_bot_account(self):
        """Bot hesabı oluştur"""
        print("🤖 LICHESS BOT HESABI OLUŞTURMA")
        print("=" * 50)
        
        instructions = """
🎯 LICHESS BOT HESABI OLUŞTURMA ADIMLARI:

1️⃣ Lichess'te Bot Hesabı Oluşturun:
   - https://lichess.org adresine gidin
   - "Kaydol" tıklayın
   - Kullanıcı adı: deniz79_bot (bot için özel)
   - Email: bot için özel email
   - Şifre: güçlü şifre
   - "Bot hesabı oluştur" seçeneğini işaretleyin

2️⃣ Bot API Token Alın:
   - Bot hesabına giriş yapın
   - Profil → Ayarlar → API
   - "Bot API Token Oluştur" tıklayın
   - Token'ı güvenli bir yere kaydedin

3️⃣ Bot Kodunu Lichess API'ye Uygun Hale Getirin:
   - Bot kodunuzu Lichess API formatına çevirin
   - UCI protokolü kullanın
   - WebSocket bağlantısı kurun

4️⃣ Bot Sunucusu Kurun:
   - Bot kodunuzu çalıştıracak sunucu
   - 7/24 çalışır durumda olmalı
   - Lichess API'ye bağlanabilmeli

5️⃣ Botu Lichess'e Kaydedin:
   - Bot API ile Lichess'e bağlanın
   - Bot bilgilerini gönderin
   - Test oyunları oynayın

6️⃣ Bot Arena'ya Katılın:
   - Bot arena'da oynamaya başlayın
   - Diğer botlarla karşılaşın
   - Rating kazanın

⚠️  ÖNEMLİ NOTLAR:
- Bot hesabı normal hesaptan farklıdır
- API token güvenli tutulmalıdır
- Bot sunucusu sürekli çalışmalıdır
- Lichess kurallarına uygun olmalıdır
"""
        
        print(instructions)
        
    def create_bot_code(self):
        """Lichess API uyumlu bot kodu oluştur"""
        print("\n💻 LICHESS API UYUMLU BOT KODU")
        print("=" * 50)
        
        bot_code = '''#!/usr/bin/env python3
"""
Lichess Bot API Uyumlu Bot Kodu
"""

import asyncio
import aiohttp
import chess
import chess.engine
import json
import logging
from typing import Optional

class LichessBot:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.session = None
        self.engine = None
        self.game_id = None
        
    async def start(self):
        """Bot'u başlat"""
        self.session = aiohttp.ClientSession()
        self.engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
        
        # Lichess API'ye bağlan
        await self.connect_to_lichess()
        
    async def connect_to_lichess(self):
        """Lichess API'ye bağlan"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        async with self.session.get(
            f"https://lichess.org/api/stream/game",
            headers=headers
        ) as response:
            async for line in response.content:
                if line:
                    game_data = json.loads(line.decode())
                    await self.handle_game_event(game_data)
                    
    async def handle_game_event(self, event):
        """Oyun olaylarını işle"""
        if event.get("type") == "gameStart":
            self.game_id = event["game"]["id"]
            await self.play_game()
            
    async def play_game(self):
        """Oyun oyna"""
        board = chess.Board()
        
        while not board.is_game_over():
            if board.turn == chess.WHITE:  # Bot'un sırası
                move = await self.get_best_move(board)
                await self.make_move(move)
                
    async def get_best_move(self, board: chess.Board) -> chess.Move:
        """En iyi hamleyi bul"""
        result = await self.engine.play(
            board, 
            chess.engine.Limit(time=2.0, depth=20)
        )
        return result.move
        
    async def make_move(self, move: chess.Move):
        """Hamle yap"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        data = {"move": move.uci()}
        
        async with self.session.post(
            f"https://lichess.org/api/bot/game/{self.game_id}/move/{move.uci()}",
            headers=headers
        ) as response:
            if response.status == 200:
                print(f"Hamle yapıldı: {move.uci()}")
            else:
                print(f"Hamle hatası: {response.status}")

async def main():
    """Ana fonksiyon"""
    api_token = "YOUR_BOT_API_TOKEN_HERE"  # Bot API token'ınızı buraya yazın
    
    bot = LichessBot(api_token)
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        # Bot kodunu dosyaya kaydet
        with open("lichess_bot.py", "w", encoding="utf-8") as f:
            f.write(bot_code)
            
        print("✅ Lichess bot kodu oluşturuldu: lichess_bot.py")
        
        return bot_code
        
    def create_deployment_guide(self):
        """Bot deployment rehberi oluştur"""
        print("\n🚀 BOT DEPLOYMENT REHBERİ")
        print("=" * 50)
        
        guide = """
🎯 BOT SUNUCU KURULUMU:

1️⃣ Sunucu Seçimi:
   - Heroku (ücretsiz)
   - Railway (ücretsiz)
   - DigitalOcean ($5/ay)
   - AWS EC2 (ücretsiz tier)

2️⃣ Heroku Kurulumu (En Kolay):
   - Heroku hesabı oluşturun
   - Heroku CLI kurun
   - Bot kodunu Heroku'ya yükleyin
   - Environment variables ekleyin

3️⃣ Railway Kurulumu:
   - Railway hesabı oluşturun
   - GitHub repository'yi bağlayın
   - Otomatik deployment

4️⃣ Environment Variables:
   - LICHESS_BOT_TOKEN=your_api_token
   - STOCKFISH_PATH=/app/stockfish
   - BOT_NAME=DenizYetik-HybridBot

5️⃣ Bot Başlatma:
   - Sunucuda bot kodunu çalıştırın
   - Lichess API'ye bağlanın
   - Test oyunları oynayın

6️⃣ Monitoring:
   - Bot loglarını takip edin
   - Hata durumlarını kontrol edin
   - Performans metriklerini izleyin

📋 GEREKSİNİMLER:
- Python 3.8+
- aiohttp
- python-chess
- stockfish
- 7/24 internet bağlantısı
"""
        
        print(guide)
        
        # requirements.txt oluştur
        requirements = """aiohttp>=3.8.0
python-chess>=1.9.0
asyncio
logging
"""
        
        with open("lichess_requirements.txt", "w") as f:
            f.write(requirements)
            
        print("✅ Lichess requirements oluşturuldu: lichess_requirements.txt")

def main():
    """Ana fonksiyon"""
    print("🤖 LICHESS BOT API KURULUM SİSTEMİ")
    print("=" * 60)
    
    bot_api = LichessBotAPI()
    
    # Bot hesabı oluşturma talimatları
    bot_api.create_bot_account()
    
    # Bot kodu oluştur
    bot_api.create_bot_code()
    
    # Deployment rehberi
    bot_api.create_deployment_guide()
    
    print("\n🎯 SONRAKI ADIMLAR:")
    print("=" * 50)
    print("1. Lichess'te bot hesabı oluşturun")
    print("2. API token alın")
    print("3. Bot kodunu sunucuya yükleyin")
    print("4. Bot'u çalıştırın")
    print("5. Lichess'te test edin")
    
    print("\n💡 İPUCU:")
    print("Heroku veya Railway kullanarak ücretsiz bot sunucusu kurabilirsiniz!")
    
    print("\n🎉 BOT API KURULUMU TAMAMLANDI!")

if __name__ == "__main__":
    main()
