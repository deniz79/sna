#!/usr/bin/env python3
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
