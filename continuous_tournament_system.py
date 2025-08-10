#!/usr/bin/env python3
"""
Sürekli Turnuva Sistemi
Her maçı otomatik kaydeder ve sürekli yeni maçlar başlatır
"""

import chess
import chess.engine
import sqlite3
import json
import pickle
import hashlib
import time
import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import signal
import sys

@dataclass
class TournamentResult:
    """Turnuva sonucu"""
    tournament_id: str
    games_played: int
    wins: int
    draws: int
    losses: int
    win_rate: float
    total_moves: int
    average_game_length: float
    learning_insights: List[str]
    timestamp: datetime

class VisualBoard:
    """Görsel tahta gösterimi"""
    def __init__(self):
        self.piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
    
    def display_board(self, board: chess.Board, move_info: str = "", evaluation: str = ""):
        """Tahtayı göster"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(" " * 20 + "8 ┌───┬───┬───┬───┬───┬───┬───┬───┐")
        for rank in range(7, -1, -1):
            row = f" " * 20 + f"{rank + 1} │"
            for file in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                if piece:
                    symbol = self.piece_symbols[piece.symbol()]
                    color = " " if piece.color else " "
                    row += f"{color}{symbol}{color}│"
                else:
                    row += "   │"
            print(row)
            if rank > 0:
                print(" " * 20 + "  ├───┼───┼───┼───┼───┼───┼───┼───┤")
        print(" " * 20 + "  └───┴───┴───┴───┴───┴───┴───┴───┘")
        print(" " * 20 + "    a   b   c   d   e   f   g   h")
        
        if move_info:
            print(f"\n{move_info}")
        if evaluation:
            print(f"Değerlendirme: {evaluation}")
        
        # Oyun durumu
        if board.is_checkmate():
            print("♔ MAT!")
        elif board.is_stalemate():
            print("🤝 PAT!")
        elif board.is_check():
            print("⚡ ŞAH!")

class ContinuousTournamentSystem:
    """Sürekli turnuva sistemi"""
    
    def __init__(self):
        self.database_path = Path("data/continuous_tournament_database.db")
        self.engine_path = "/opt/homebrew/bin/stockfish"
        self.engine = None
        self.visual_board = VisualBoard()
        self.games_per_tournament = 5
        self.analysis_depth = 25
        self.analysis_time = 8.0
        self.running = True
        
        # Sinyal yakalayıcı
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self._initialize_database()
        self._initialize_engine()
    
    def _signal_handler(self, signum, frame):
        """Sinyal yakalayıcı"""
        print(f"\n🛑 Turnuva sistemi durduruluyor...")
        self.running = False
        if self.engine:
            self.engine.quit()
        sys.exit(0)
    
    def _initialize_engine(self):
        """Motor başlat"""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            self.engine.configure({
                "Threads": 4,
                "Hash": 1024
            })
            print(f"✅ Stockfish motoru başlatıldı")
        except Exception as e:
            print(f"❌ Motor başlatma hatası: {e}")
            sys.exit(1)
    
    def _initialize_database(self):
        """Veritabanı başlat"""
        self.database_path.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Turnuva sonuçları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id TEXT UNIQUE,
                games_played INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                win_rate REAL,
                total_moves INTEGER,
                average_game_length REAL,
                learning_insights TEXT,
                timestamp DATETIME
            )
        ''')
        
        # Oyun sonuçları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id TEXT,
                game_id TEXT,
                result TEXT,
                moves TEXT,
                position_analyses BLOB,
                mistakes TEXT,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Veritabanı başlatıldı: {self.database_path}")
    
    def _get_winner(self, result: str) -> str:
        """Kazananı belirle"""
        if result == "1-0":
            return "Beyaz (Bot)"
        elif result == "0-1":
            return "Siyah (Stockfish)"
        else:
            return "Beraberlik"
    
    def play_single_game(self, game_number: int, tournament_id: str) -> Dict:
        """Tek oyun oyna"""
        board = chess.Board()
        moves = []
        position_analyses = []
        mistakes = []
        moves_without_capture = 0
        
        print(f"\n🎮 OYUN {game_number} BAŞLIYOR")
        print("=" * 50)
        
        while not board.is_game_over():
            # 50 hamle kuralı kontrolü
            if moves_without_capture >= 100:  # 50 tam hamle = 100 yarı hamle
                print("   ⏰ 50 hamle kuralı! Beraberlik")
                break
            
            # Bot hamlesi (Beyaz)
            if board.turn == chess.WHITE:
                start_time = time.time()
                result = self.engine.play(board, chess.engine.Limit(time=self.analysis_time, depth=self.analysis_depth))
                analysis_time = time.time() - start_time
                
                move = result.move
                evaluation = result.info.get('score', None)
                if evaluation:
                    eval_value = evaluation.white().score(mate_score=10000) / 100.0
                else:
                    eval_value = None
                
                move_info = f"🎯 Bot: {board.san(move)} (Analiz: {analysis_time:.2f}s)"
                if eval_value is not None:
                    move_info += f" [Eval: {eval_value:.2f}]"
                
                print(move_info)
                
                # Hamle bilgilerini kaydet
                move_data = {
                    'san': board.san(move),
                    'uci': move.uci(),
                    'analysis_time': analysis_time,
                    'evaluation': eval_value
                }
                moves.append(move_data)
                
                # 50 hamle kuralı kontrolü
                if board.is_capture(move):
                    moves_without_capture = 0
                else:
                    moves_without_capture += 1
                
                board.push(move)
                
                # Tahta gösterimi
                self.visual_board.display_board(board, move_info, f"Eval: {eval_value:.2f}" if eval_value else "")
                time.sleep(1)
            
            # Stockfish hamlesi (Siyah)
            else:
                start_time = time.time()
                result = self.engine.play(board, chess.engine.Limit(time=2.0))
                think_time = time.time() - start_time
                
                move = result.move
                move_info = f"🤖 Stockfish: {board.san(move)} (Düşünme: {think_time:.2f}s)"
                print(move_info)
                
                # Hamle bilgilerini kaydet
                move_data = {
                    'san': board.san(move),
                    'uci': move.uci(),
                    'think_time': think_time
                }
                moves.append(move_data)
                
                # 50 hamle kuralı kontrolü
                if board.is_capture(move):
                    moves_without_capture = 0
                else:
                    moves_without_capture += 1
                
                board.push(move)
                
                # Tahta gösterimi
                self.visual_board.display_board(board, move_info, "")
                time.sleep(1)
        
        # Oyun sonucu
        result = board.result()
        winner = self._get_winner(result)
        
        print(f"\n🏁 OYUN {game_number} SONUCU: {result}")
        print(f"📊 Toplam hamle: {len(moves)}")
        print(f"🏆 KAZANAN: {winner}")
        
        # Skor bilgisi
        if result == "1-0":
            print(f"🎉 BEYAZ KAZANDI! (Bot)")
        elif result == "0-1":
            print(f"😔 SİYAH KAZANDI! (Stockfish)")
        else:
            print(f"🤝 BERABERLİK!")
        
        # Final tahta gösterimi
        final_info = f"Oyun sonucu: {result} | Kazanan: {winner} | Hamle: {len(moves)}"
        self.visual_board.display_board(board, final_info, "")
        time.sleep(3)
        
        return {
            'result': result,
            'winner': winner,
            'moves': moves,
            'position_analyses': position_analyses,
            'mistakes': mistakes,
            'final_fen': board.fen()
        }
    
    def _save_game_result(self, tournament_id: str, game_result: Dict):
        """Oyun sonucunu kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        game_id = f"{tournament_id}_game_{len(game_result['moves'])}"
        
        cursor.execute('''
            INSERT INTO game_results 
            (tournament_id, game_id, result, moves, position_analyses, mistakes, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            tournament_id,
            game_id,
            game_result['result'],
            json.dumps(game_result['moves']),
            pickle.dumps(game_result['position_analyses']),
            json.dumps(game_result['mistakes']),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"💾 Oyun kaydedildi: {game_id}")
    
    def _save_tournament_result(self, tournament_result: TournamentResult):
        """Turnuva sonucunu kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tournament_results 
            (tournament_id, games_played, wins, draws, losses, win_rate, 
             total_moves, average_game_length, learning_insights, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tournament_result.tournament_id,
            tournament_result.games_played,
            tournament_result.wins,
            tournament_result.draws,
            tournament_result.losses,
            tournament_result.win_rate,
            tournament_result.total_moves,
            tournament_result.average_game_length,
            json.dumps(tournament_result.learning_insights),
            tournament_result.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"💾 Turnuva kaydedildi: {tournament_result.tournament_id}")
    
    def play_tournament(self, tournament_id: str) -> TournamentResult:
        """Turnuva oyna"""
        print(f"\n🏆 TURNUVA {tournament_id} BAŞLIYOR")
        print("=" * 60)
        
        wins = 0
        draws = 0
        losses = 0
        total_moves = 0
        learning_insights = []
        
        for game_num in range(1, self.games_per_tournament + 1):
            if not self.running:
                break
                
            game_result = self.play_single_game(game_num, tournament_id)
            
            # Sonuçları say
            if game_result['result'] == "1-0":
                wins += 1
                print(f"🎉 OYUN {game_num}: KAZANDIK! (Beyaz)")
            elif game_result['result'] == "0-1":
                losses += 1
                print(f"😔 OYUN {game_num}: KAYBETTİK! (Siyah)")
            else:
                draws += 1
                print(f"🤝 OYUN {game_num}: BERABERLİK!")
            
            print(f"   Kazanan: {game_result['winner']}")
            print(f"   Hamle sayısı: {len(game_result['moves'])}")
            
            total_moves += len(game_result['moves'])
            
            # Oyun sonucunu hemen kaydet
            self._save_game_result(tournament_id, game_result)
            
            print(f"📊 Turnuva durumu: {wins}K {draws}B {losses}Y")
            print("-" * 40)
            
            # Kısa bir bekleme
            time.sleep(2)
        
        # Turnuva sonucu
        games_played = self.games_per_tournament
        win_rate = wins / games_played
        average_game_length = total_moves / games_played
        
        tournament_result = TournamentResult(
            tournament_id=tournament_id,
            games_played=games_played,
            wins=wins,
            draws=draws,
            losses=losses,
            win_rate=win_rate,
            total_moves=total_moves,
            average_game_length=average_game_length,
            learning_insights=learning_insights,
            timestamp=datetime.now()
        )
        
        # Turnuva sonucunu kaydet
        self._save_tournament_result(tournament_result)
        
        print(f"\n🏆 TURNUVA {tournament_id} SONUCU:")
        print(f"   Oyunlar: {games_played}")
        print(f"   Kazanma: {wins}")
        print(f"   Beraberlik: {draws}")
        print(f"   Kaybetme: {losses}")
        print(f"   Kazanma oranı: {win_rate:.1%}")
        print(f"   Ortalama oyun uzunluğu: {average_game_length:.1f} hamle")
        print(f"   Turnuva skoru: {wins}K {draws}B {losses}Y")
        
        return tournament_result
    
    def run_continuous_tournaments(self):
        """Sürekli turnuvalar çalıştır"""
        tournament_count = 0
        
        print("🚀 SÜREKLİ TURNUVA SİSTEMİ BAŞLATIYOR")
        print("=" * 60)
        print("💡 Her turnuva otomatik kaydedilir")
        print("💡 Ctrl+C ile durdurabilirsiniz")
        print("=" * 60)
        
        while self.running:
            tournament_count += 1
            tournament_id = f"CT{tournament_count:03d}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            try:
                tournament_result = self.play_tournament(tournament_id)
                
                print(f"\n📈 GENEL DURUM:")
                print(f"   Tamamlanan turnuva: {tournament_count}")
                print(f"   Son turnuva kazanma oranı: {tournament_result.win_rate:.1%}")
                
                # Kullanıcıya devam etmek isteyip istemediğini sor
                if tournament_count % 3 == 0:  # Her 3 turnuvada bir
                    print(f"\n⏸️  {tournament_count} turnuva tamamlandı. Devam etmek istiyor musunuz? (y/n): ", end="")
                    try:
                        response = input().lower().strip()
                        if response != 'y' and response != 'yes':
                            print("🛑 Turnuva sistemi durduruluyor...")
                            break
                    except KeyboardInterrupt:
                        print("\n🛑 Turnuva sistemi durduruluyor...")
                        break
                
                print(f"\n🔄 Sonraki turnuva başlatılıyor...")
                time.sleep(3)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Turnuva sistemi durduruluyor...")
                break
            except Exception as e:
                print(f"❌ Hata: {e}")
                print("🔄 Turnuva yeniden başlatılıyor...")
                time.sleep(5)
        
        print(f"\n🏁 TOPLAM {tournament_count} TURNUVA TAMAMLANDI")
        print("✅ Tüm sonuçlar kaydedildi")
    
    def close(self):
        """Sistemi kapat"""
        if self.engine:
            self.engine.quit()
        print("👋 Sistem kapatıldı")

def main():
    """Ana fonksiyon"""
    system = ContinuousTournamentSystem()
    
    try:
        system.run_continuous_tournaments()
    except KeyboardInterrupt:
        print(f"\n🛑 Kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
    finally:
        system.close()

if __name__ == "__main__":
    main()
