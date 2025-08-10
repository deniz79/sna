#!/usr/bin/env python3
"""
Detaylı Tek Maç Sistemi
Her hamleyi detaylı gösterir ve süre bilgilerini verir
"""

import chess
import chess.engine
import sqlite3
import json
import pickle
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

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

class DetailedSingleMatch:
    """Detaylı tek maç sistemi"""
    
    def __init__(self):
        self.database_path = Path("data/detailed_single_match.db")
        self.engine_path = "/opt/homebrew/bin/stockfish"
        self.engine = None
        self.visual_board = VisualBoard()
        self.analysis_depth = 25
        self.analysis_time = 8.0
        
        self._initialize_database()
        self._initialize_engine()
    
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
            return False
        return True
    
    def _initialize_database(self):
        """Veritabanı başlat"""
        self.database_path.parent.mkdir(exist_ok=True)
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Oyun sonuçları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT UNIQUE,
                result TEXT,
                moves TEXT,
                total_time REAL,
                average_move_time REAL,
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
    
    def _get_square_name(self, square: int) -> str:
        """Kare adını al"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        return f"{chr(97 + file)}{rank + 1}"
    
    def _get_piece_name(self, piece: chess.Piece) -> str:
        """Taş adını al"""
        piece_names = {
            'P': 'Piyon', 'N': 'At', 'B': 'Fil', 'R': 'Kale', 'Q': 'Vezir', 'K': 'Şah',
            'p': 'Piyon', 'n': 'At', 'b': 'Fil', 'r': 'Kale', 'q': 'Vezir', 'k': 'Şah'
        }
        return piece_names.get(piece.symbol(), 'Bilinmeyen')
    
    def play_detailed_match(self):
        """Detaylı maç oyna"""
        board = chess.Board()
        moves = []
        moves_without_capture = 0
        total_start_time = time.time()
        
        print("🎮 DETAYLI TEK MAÇ BAŞLIYOR")
        print("=" * 60)
        print("💡 Her hamle detaylı gösterilecek")
        print("💡 Süre bilgileri verilecek")
        print("💡 Taş hareketleri açıklanacak")
        print("=" * 60)
        
        move_count = 0
        
        while not board.is_game_over():
            move_count += 1
            
            # 50 hamle kuralı kontrolü
            if moves_without_capture >= 100:  # 50 tam hamle = 100 yarı hamle
                print(f"\n⏰ 50 hamle kuralı! Beraberlik")
                break
            
            print(f"\n🎯 HAMLE {move_count}")
            print("-" * 40)
            
            # Bot hamlesi (Beyaz)
            if board.turn == chess.WHITE:
                print(f"🤖 SIRA: Beyaz (Bot)")
                
                start_time = time.time()
                result = self.engine.play(board, chess.engine.Limit(time=self.analysis_time, depth=self.analysis_depth))
                analysis_time = time.time() - start_time
                
                move = result.move
                evaluation = result.info.get('score', None)
                if evaluation:
                    eval_value = evaluation.white().score(mate_score=10000) / 100.0
                else:
                    eval_value = None
                
                # Hamle detayları
                move_san = board.san(move)
                move_uci = move.uci()
                from_square = move.from_square
                to_square = move.to_square
                
                # Taş bilgileri
                piece = board.piece_at(from_square)
                piece_name = self._get_piece_name(piece) if piece else "Bilinmeyen"
                from_square_name = self._get_square_name(from_square)
                to_square_name = self._get_square_name(to_square)
                
                # Özel hamle türleri
                move_type = ""
                if board.is_capture(move):
                    captured_piece = board.piece_at(to_square)
                    captured_name = self._get_piece_name(captured_piece) if captured_piece else "Bilinmeyen"
                    move_type = f"🎯 {captured_name} ALDI"
                elif board.is_castling(move):
                    move_type = "🏰 ROK YAPTI"
                elif board.is_en_passant(move):
                    move_type = "⚡ GEÇERKEN ALDI"
                elif move.promotion:
                    promotion_piece = chess.piece_symbol(move.promotion)
                    promotion_name = self._get_piece_name(chess.Piece(chess.WHITE, move.promotion))
                    move_type = f"👑 {promotion_name} OLDU"
                
                # Hamle bilgilerini yazdır
                print(f"📝 Hamle: {move_san}")
                print(f"🔤 UCI: {move_uci}")
                print(f"🎯 Taş: {piece_name}")
                print(f"📍 Nereden: {from_square_name}")
                print(f"🎯 Nereye: {to_square_name}")
                if move_type:
                    print(f"⚡ Tür: {move_type}")
                print(f"⏱️  Analiz süresi: {analysis_time:.2f} saniye")
                if eval_value is not None:
                    print(f"📊 Değerlendirme: {eval_value:.2f}")
                
                # Hamle bilgilerini kaydet
                move_data = {
                    'move_number': move_count,
                    'player': 'Bot',
                    'color': 'Beyaz',
                    'san': move_san,
                    'uci': move_uci,
                    'from_square': from_square_name,
                    'to_square': to_square_name,
                    'piece': piece_name,
                    'move_type': move_type,
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
                eval_str = f"{eval_value:.2f}" if eval_value else "Bilinmiyor"
                move_info = f"Hamle {move_count}: Bot {move_san} | Süre: {analysis_time:.2f}s | Eval: {eval_str}"
                self.visual_board.display_board(board, move_info, eval_str)
                
                print(f"✅ Hamle tamamlandı!")
                time.sleep(2)
            
            # Stockfish hamlesi (Siyah)
            else:
                print(f"🤖 SIRA: Siyah (Stockfish)")
                
                start_time = time.time()
                result = self.engine.play(board, chess.engine.Limit(time=2.0))
                think_time = time.time() - start_time
                
                move = result.move
                
                # Hamle detayları
                move_san = board.san(move)
                move_uci = move.uci()
                from_square = move.from_square
                to_square = move.to_square
                
                # Taş bilgileri
                piece = board.piece_at(from_square)
                piece_name = self._get_piece_name(piece) if piece else "Bilinmeyen"
                from_square_name = self._get_square_name(from_square)
                to_square_name = self._get_square_name(to_square)
                
                # Özel hamle türleri
                move_type = ""
                if board.is_capture(move):
                    captured_piece = board.piece_at(to_square)
                    captured_name = self._get_piece_name(captured_piece) if captured_piece else "Bilinmeyen"
                    move_type = f"🎯 {captured_name} ALDI"
                elif board.is_castling(move):
                    move_type = "🏰 ROK YAPTI"
                elif board.is_en_passant(move):
                    move_type = "⚡ GEÇERKEN ALDI"
                elif move.promotion:
                    promotion_piece = chess.piece_symbol(move.promotion)
                    promotion_name = self._get_piece_name(chess.Piece(chess.WHITE, move.promotion))
                    move_type = f"👑 {promotion_name} OLDU"
                
                # Hamle bilgilerini yazdır
                print(f"📝 Hamle: {move_san}")
                print(f"🔤 UCI: {move_uci}")
                print(f"🎯 Taş: {piece_name}")
                print(f"📍 Nereden: {from_square_name}")
                print(f"🎯 Nereye: {to_square_name}")
                if move_type:
                    print(f"⚡ Tür: {move_type}")
                print(f"⏱️  Düşünme süresi: {think_time:.2f} saniye")
                
                # Hamle bilgilerini kaydet
                move_data = {
                    'move_number': move_count,
                    'player': 'Stockfish',
                    'color': 'Siyah',
                    'san': move_san,
                    'uci': move_uci,
                    'from_square': from_square_name,
                    'to_square': to_square_name,
                    'piece': piece_name,
                    'move_type': move_type,
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
                move_info = f"Hamle {move_count}: Stockfish {move_san} | Süre: {think_time:.2f}s"
                self.visual_board.display_board(board, move_info, "")
                
                print(f"✅ Hamle tamamlandı!")
                time.sleep(2)
        
        # Oyun sonucu
        total_time = time.time() - total_start_time
        result = board.result()
        winner = self._get_winner(result)
        
        print(f"\n🏁 OYUN SONUCU")
        print("=" * 60)
        print(f"📊 Sonuç: {result}")
        print(f"🏆 Kazanan: {winner}")
        print(f"📈 Toplam hamle: {len(moves)}")
        print(f"⏱️  Toplam süre: {total_time:.2f} saniye")
        print(f"📊 Ortalama hamle süresi: {total_time/len(moves):.2f} saniye")
        
        # Final tahta gösterimi
        final_info = f"Oyun sonucu: {result} | Kazanan: {winner} | Hamle: {len(moves)} | Süre: {total_time:.2f}s"
        self.visual_board.display_board(board, final_info, "")
        
        # Hamle özeti
        print(f"\n📝 HAMLE ÖZETİ")
        print("=" * 60)
        for i, move_data in enumerate(moves, 1):
            player = move_data['player']
            san = move_data['san']
            piece = move_data['piece']
            from_sq = move_data['from_square']
            to_sq = move_data['to_square']
            move_type = move_data.get('move_type', '')
            
            time_info = ""
            if 'analysis_time' in move_data:
                time_info = f" | Analiz: {move_data['analysis_time']:.2f}s"
            elif 'think_time' in move_data:
                time_info = f" | Düşünme: {move_data['think_time']:.2f}s"
            
            eval_info = ""
            if 'evaluation' in move_data and move_data['evaluation'] is not None:
                eval_info = f" | Eval: {move_data['evaluation']:.2f}"
            
            print(f"{i:2d}. {player:10} {san:6} ({piece:6} {from_sq}→{to_sq}) {move_type}{time_info}{eval_info}")
        
        # Oyunu kaydet
        self._save_game_result(moves, result, total_time)
        
        return {
            'result': result,
            'winner': winner,
            'moves': moves,
            'total_time': total_time,
            'move_count': len(moves)
        }
    
    def _save_game_result(self, moves: List[Dict], result: str, total_time: float):
        """Oyun sonucunu kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        game_id = f"detailed_match_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        average_move_time = total_time / len(moves) if moves else 0
        
        cursor.execute('''
            INSERT INTO game_results 
            (game_id, result, moves, total_time, average_move_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            game_id,
            result,
            json.dumps(moves),
            total_time,
            average_move_time,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"💾 Oyun kaydedildi: {game_id}")
    
    def close(self):
        """Sistemi kapat"""
        if self.engine:
            self.engine.quit()
        print("👋 Sistem kapatıldı")

def main():
    """Ana fonksiyon"""
    print("🎮 DETAYLI TEK MAÇ SİSTEMİ")
    print("=" * 60)
    
    system = DetailedSingleMatch()
    
    try:
        result = system.play_detailed_match()
        
        print(f"\n🎉 MAÇ TAMAMLANDI!")
        print(f"🏆 Kazanan: {result['winner']}")
        print(f"📊 Hamle sayısı: {result['move_count']}")
        print(f"⏱️  Toplam süre: {result['total_time']:.2f} saniye")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
    finally:
        system.close()

if __name__ == "__main__":
    main()
