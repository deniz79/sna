#!/usr/bin/env python3
"""
Turnuva Öğrenme Sistemi
Kazanana kadar tekrarlayan, görsel tahta gösteren turnuva sistemi
"""

import chess
import chess.engine
import chess.pgn
import json
import sqlite3
import time
import logging
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import pickle
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        """Tahtayı görsel olarak göster"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("=" * 80)
        print("🎯 TURNUVA ÖĞRENME SİSTEMİ - GÖRSEL TAHTA")
        print("=" * 80)
        
        if move_info:
            print(f"📊 {move_info}")
        if evaluation:
            print(f"🎯 {evaluation}")
        
        print("\n" + " " * 20 + "8 ┌───┬───┬───┬───┬───┬───┬───┬───┐")
        
        for rank in range(7, -1, -1):
            row = f" " * 20 + f"{rank + 1} │"
            for file in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                
                if piece:
                    symbol = self.piece_symbols[piece.symbol()]
                    if piece.color == chess.WHITE:
                        row += f" {symbol} │"
                    else:
                        row += f" {symbol} │"
                else:
                    # Alternatif renkli kareler
                    if (rank + file) % 2 == 0:
                        row += "   │"
                    else:
                        row += " █ │"
            
            print(row)
            if rank > 0:
                print(" " * 20 + "  ├───┼───┼───┼───┼───┼───┼───┼───┤")
        
        print(" " * 20 + "  └───┴───┴───┴───┴───┴───┴───┴───┘")
        print(" " * 20 + "    a   b   c   d   e   f   g   h")
        
        # Oyun durumu
        if board.is_check():
            print("\n⚠️  ŞAH!")
        if board.is_checkmate():
            print("\n🏁 ŞAH MAT!")
        elif board.is_stalemate():
            print("\n🤝 PAT!")
        elif board.is_insufficient_material():
            print("\n🤝 YETERSİZ MATERYAL!")
        
        print("=" * 80)

class TournamentLearningSystem:
    """Turnuva öğrenme sistemi"""
    
    def __init__(self):
        self.stockfish = None
        self.database_path = Path("data/tournament_database.db")
        self.positions_cache = {}
        self.mistakes_database = {}
        self.tournament_history = []
        self.visual_board = VisualBoard()
        
        # Turnuva parametreleri
        self.games_per_tournament = 5
        self.target_win_rate = 0.6  # %60 kazanma oranı
        self.max_tournaments = 50
        self.analysis_depth = 25
        self.analysis_time = 8.0
        
        self._initialize_engine()
        self._initialize_database()
        self._load_learning_data()
    
    def _initialize_engine(self):
        """Stockfish motorunu başlat"""
        try:
            self.stockfish = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
            self.stockfish.configure({
                "Threads": 8,
                "Hash": 4096,
                "MultiPV": 3,
                "Contempt": 0
            })
            logger.info("Stockfish turnuva modunda başlatıldı")
        except Exception as e:
            logger.error(f"Stockfish başlatma hatası: {e}")
    
    def _initialize_database(self):
        """Turnuva veritabanını başlat"""
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
                position_analyses TEXT,
                mistakes TEXT,
                timestamp DATETIME
            )
        ''')
        
        # Pozisyon analizi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_hash TEXT UNIQUE,
                fen TEXT,
                evaluation REAL,
                best_moves TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                timestamp DATETIME
            )
        ''')
        
        # Hata analizi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mistakes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_hash TEXT,
                move_played TEXT,
                move_evaluation REAL,
                best_move TEXT,
                best_evaluation REAL,
                mistake_type TEXT,
                severity REAL,
                tournament_id TEXT,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Turnuva veritabanı başlatıldı")
    
    def _load_learning_data(self):
        """Öğrenme verilerini yükle"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Pozisyon cache'ini yükle
        cursor.execute('SELECT position_hash, fen, evaluation, best_moves FROM position_analyses')
        for row in cursor.fetchall():
            position_hash, fen, evaluation, best_moves = row
            self.positions_cache[position_hash] = {
                'fen': fen,
                'evaluation': evaluation,
                'best_moves': json.loads(best_moves) if best_moves else []
            }
        
        # Hata veritabanını yükle
        cursor.execute('SELECT position_hash, move_played, best_move, mistake_type, severity FROM mistakes')
        for row in cursor.fetchall():
            position_hash, move_played, best_move, mistake_type, severity = row
            if position_hash not in self.mistakes_database:
                self.mistakes_database[position_hash] = []
            self.mistakes_database[position_hash].append({
                'move_played': move_played,
                'best_move': best_move,
                'mistake_type': mistake_type,
                'severity': severity
            })
        
        conn.close()
        logger.info(f"Öğrenme verileri yüklendi: {len(self.positions_cache)} pozisyon, {len(self.mistakes_database)} hata")
    
    def _get_position_hash(self, board: chess.Board) -> str:
        """Pozisyon hash'i oluştur"""
        return hashlib.md5(board.fen().encode()).hexdigest()
    
    def _get_winner(self, result: str) -> str:
        """Kazananı belirle"""
        if result == "1-0":
            return "Beyaz (Bot)"
        elif result == "0-1":
            return "Siyah (Stockfish)"
        else:
            return "Beraberlik"
    
    def deep_position_analysis(self, board: chess.Board) -> Dict:
        """Derin pozisyon analizi"""
        position_hash = self._get_position_hash(board)
        
        # Cache'den kontrol et
        if position_hash in self.positions_cache:
            cached_data = self.positions_cache[position_hash]
            return {
                'position_hash': position_hash,
                'evaluation': cached_data['evaluation'],
                'best_moves': cached_data['best_moves'],
                'cached': True
            }
        
        # Stockfish ile derin analiz
        if self.stockfish:
            try:
                result = self.stockfish.analyse(
                    board, 
                    chess.engine.Limit(depth=self.analysis_depth, time=self.analysis_time),
                    multipv=3
                )
                
                # En iyi hamleleri çıkar
                best_moves = []
                for i, analysis in enumerate(result):
                    if i < 3:
                        move_san = board.san(analysis['pv'][0]) if analysis['pv'] else "N/A"
                        score = analysis['score'].relative.score(mate_score=10000) / 100.0
                        best_moves.append((move_san, score))
                
                # Ana değerlendirme
                main_evaluation = result[0]['score'].relative.score(mate_score=10000) / 100.0
                
                analysis = {
                    'position_hash': position_hash,
                    'evaluation': main_evaluation,
                    'best_moves': best_moves,
                    'cached': False
                }
                
                # Cache'e kaydet
                self.positions_cache[position_hash] = {
                    'fen': board.fen(),
                    'evaluation': main_evaluation,
                    'best_moves': best_moves
                }
                
                # Veritabanına kaydet
                self._save_position_analysis(analysis)
                
                return analysis
                
            except Exception as e:
                logger.error(f"Derin analiz hatası: {e}")
        
        return {
            'position_hash': position_hash,
            'evaluation': 0.0,
            'best_moves': [],
            'cached': False
        }
    
    def _save_position_analysis(self, analysis: Dict):
        """Pozisyon analizini kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO position_analyses 
            (position_hash, fen, evaluation, best_moves, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            analysis['position_hash'],
            chess.Board().fen(),  # Geçici FEN
            analysis['evaluation'],
            json.dumps(analysis['best_moves']),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_best_move_with_learning(self, board: chess.Board) -> Optional[chess.Move]:
        """Öğrenme ile en iyi hamleyi al"""
        position_hash = self._get_position_hash(board)
        
        # Derin analiz yap
        analysis = self.deep_position_analysis(board)
        
        # Önceki hataları kontrol et
        if position_hash in self.mistakes_database:
            mistakes = self.mistakes_database[position_hash]
            
            # Hatalı hamleleri filtrele
            bad_moves = set()
            for mistake in mistakes:
                bad_moves.add(mistake['move_played'])
            
            # En iyi hamleleri filtrele
            filtered_moves = []
            for move_san, score in analysis['best_moves']:
                if move_san not in bad_moves:
                    filtered_moves.append((move_san, score))
            
            if filtered_moves:
                analysis['best_moves'] = filtered_moves
        
        # En iyi hamleyi seç
        if analysis['best_moves']:
            best_move_san = analysis['best_moves'][0][0]
            try:
                best_move = board.parse_san(best_move_san)
                return best_move
            except:
                pass
        
        # Fallback: rastgele yasal hamle
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return legal_moves[0]
        
        return None
    
    def record_mistake(self, board: chess.Board, move_played: chess.Move, 
                      move_evaluation: float, best_move: chess.Move, 
                      best_evaluation: float, tournament_id: str):
        """Hatayı kaydet"""
        position_hash = self._get_position_hash(board)
        move_san = board.san(move_played)
        best_move_san = board.san(best_move)
        
        # Hata tipini belirle
        evaluation_diff = best_evaluation - move_evaluation
        if evaluation_diff > 2.0:
            mistake_type = "blunder"
            severity = 1.0
        elif evaluation_diff > 1.0:
            mistake_type = "mistake"
            severity = 0.7
        elif evaluation_diff > 0.5:
            mistake_type = "inaccuracy"
            severity = 0.4
        else:
            mistake_type = "minor"
            severity = 0.2
        
        # Hata veritabanına kaydet
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO mistakes 
            (position_hash, move_played, move_evaluation, best_move, 
             best_evaluation, mistake_type, severity, tournament_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position_hash,
            move_san,
            move_evaluation,
            best_move_san,
            best_evaluation,
            mistake_type,
            severity,
            tournament_id,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        # Cache'e ekle
        if position_hash not in self.mistakes_database:
            self.mistakes_database[position_hash] = []
        
        self.mistakes_database[position_hash].append({
            'move_played': move_san,
            'best_move': best_move_san,
            'mistake_type': mistake_type,
            'severity': severity
        })
    
    def play_single_game(self, game_number: int, tournament_id: str) -> Dict:
        """Tek oyun oyna"""
        board = chess.Board()
        moves = []
        position_analyses = []
        mistakes = []
        
        print(f"\n🎮 TURNUVA {tournament_id} - OYUN {game_number}")
        print("=" * 60)
        
        # İlk tahta gösterimi
        self.visual_board.display_board(board, "Oyun başlıyor...", "Değerlendirme: 0.00")
        time.sleep(2)
        
        while not board.is_game_over():
            move_count = len(moves) + 1
            
            if board.turn == chess.WHITE:
                # Bizim bot
                print(f"\n{move_count}. Beyaz (Öğrenen Bot) düşünüyor...")
                
                # Derin pozisyon analizi
                start_analysis = time.time()
                analysis = self.deep_position_analysis(board)
                analysis_time = time.time() - start_analysis
                
                position_analyses.append(analysis)
                
                # Hamle seçimi
                start_move = time.time()
                move = self.get_best_move_with_learning(board)
                move_time = time.time() - start_move
                
                if move:
                    san_move = board.san(move)
                    total_time = analysis_time + move_time
                    
                    # Hamle bilgisi
                    move_info = f"Hamle {move_count}: {san_move} (Beyaz)"
                    evaluation_info = f"Değerlendirme: {analysis['evaluation']:.2f} | Analiz: {analysis_time:.1f}s"
                    
                    # Tahtayı göster
                    self.visual_board.display_board(board, move_info, evaluation_info)
                    
                    # Hamle kalitesini kontrol et
                    move_evaluation = None
                    for move_san, score in analysis['best_moves']:
                        if move_san == san_move:
                            move_evaluation = score
                            break
                    
                    if move_evaluation is not None and analysis['best_moves']:
                        best_evaluation = analysis['best_moves'][0][1]
                        if move_evaluation < best_evaluation - 0.1:
                            # Hata kaydet
                            self.record_mistake(board, move, move_evaluation, 
                                              board.parse_san(analysis['best_moves'][0][0]), best_evaluation, tournament_id)
                            mistakes.append({
                                'move': move_count,
                                'move_played': san_move,
                                'move_evaluation': move_evaluation,
                                'best_move': analysis['best_moves'][0][0],
                                'best_evaluation': best_evaluation
                            })
                            print(f"   ⚠️  Hata tespit edildi ve kaydedildi!")
                    
                    board.push(move)
                    moves.append({
                        'move': move_count,
                        'color': 'white',
                        'san': san_move,
                        'uci': move.uci(),
                        'analysis_time': analysis_time,
                        'move_time': move_time,
                        'total_time': total_time,
                        'evaluation': move_evaluation
                    })
                    
                    time.sleep(1)  # Hamleyi görmek için bekle
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
                    
            else:
                # Stockfish
                print(f"\n{move_count}. Siyah (Stockfish) düşünüyor...")
                
                start_time = time.time()
                result = self.stockfish.play(board, chess.engine.Limit(time=2.0))
                end_time = time.time()
                
                if result.move:
                    san_move = board.san(result.move)
                    think_time = end_time - start_time
                    
                    # Hamle bilgisi
                    move_info = f"Hamle {move_count}: {san_move} (Siyah)"
                    evaluation_info = f"Stockfish | Düşünme: {think_time:.1f}s"
                    
                    # Tahtayı göster
                    self.visual_board.display_board(board, move_info, evaluation_info)
                    
                    board.push(result.move)
                    moves.append({
                        'move': move_count,
                        'color': 'black',
                        'san': san_move,
                        'uci': result.move.uci(),
                        'think_time': think_time,
                        'position_type': 'stockfish'
                    })
                    
                    time.sleep(1)  # Hamleyi görmek için bekle
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
        
        # Oyun sonucu
        result = board.result()
        winner = self._get_winner(result)
        
        print(f"\n🏁 OYUN SONUCU: {result}")
        print(f"📊 Toplam hamle: {len(moves)}")
        print(f"⚠️  Tespit edilen hatalar: {len(mistakes)}")
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
    
    def play_tournament(self, tournament_id: str) -> TournamentResult:
        """Turnuva oyna"""
        print(f"\n🏆 TURNUVA {tournament_id} BAŞLIYOR!")
        print("=" * 60)
        
        wins = 0
        draws = 0
        losses = 0
        total_moves = 0
        learning_insights = []
        
        for game_num in range(1, self.games_per_tournament + 1):
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
        
        # Öğrenme içgörüleri
        if game_result['mistakes']:
            for mistake in game_result['mistakes']:
                insight = f"Oyun {game_num}: {mistake['move_played']} yerine {mistake['best_move']} oynanmalı"
                learning_insights.append(insight)
        
        # Oyun sonucunu kaydet
        self._save_game_result(tournament_id, game_result)
        
        print(f"📊 Turnuva durumu: {wins}K {draws}B {losses}Y")
        print("-" * 40)
        
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
        
        if learning_insights:
            print(f"\n🎓 Öğrenme İçgörüleri ({len(learning_insights)}):")
            for insight in learning_insights[:5]:  # İlk 5'ini göster
                print(f"   • {insight}")
        
        return tournament_result
    
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
    
    def run_learning_tournaments(self):
        """Kazanana kadar turnuvalar oyna"""
        print("🚀 KAZANANA KADAR TURNUVA SİSTEMİ BAŞLIYOR!")
        print("=" * 60)
        print(f"🎯 Hedef kazanma oranı: {self.target_win_rate:.1%}")
        print(f"🎮 Turnuva başına oyun: {self.games_per_tournament}")
        print(f"🏆 Maksimum turnuva: {self.max_tournaments}")
        print("=" * 60)
        
        tournament_count = 0
        best_win_rate = 0.0
        
        while tournament_count < self.max_tournaments:
            tournament_count += 1
            tournament_id = f"T{tournament_count:03d}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            print(f"\n🏆 TURNUVA {tournament_count}/{self.max_tournaments}")
            print("=" * 50)
            
            # Turnuva oyna
            tournament_result = self.play_tournament(tournament_id)
            
            # Sonuçları kontrol et
            if tournament_result.win_rate > best_win_rate:
                best_win_rate = tournament_result.win_rate
                print(f"🏆 YENİ REKOR! En iyi kazanma oranı: {best_win_rate:.1%}")
            
            # Hedef kontrolü
            if tournament_result.win_rate >= self.target_win_rate:
                print(f"\n🎉 HEDEFE ULAŞTIK!")
                print(f"   Kazanma oranı: {tournament_result.win_rate:.1%}")
                print(f"   Hedef: {self.target_win_rate:.1%}")
                print(f"   Toplam turnuva: {tournament_count}")
                break
            
            print(f"\n📊 Genel durum:")
            print(f"   Mevcut kazanma oranı: {tournament_result.win_rate:.1%}")
            print(f"   En iyi kazanma oranı: {best_win_rate:.1%}")
            print(f"   Hedef: {self.target_win_rate:.1%}")
            print(f"   Kalan turnuva: {self.max_tournaments - tournament_count}")
            
            # Devam etmek isteyip istemediğini sor
            if tournament_count < self.max_tournaments:
                print(f"\n⏸️  Sonraki turnuvaya geçmek için Enter'a basın...")
                input()
        
        # Final raporu
        print(f"\n🏁 ÖĞRENME SİSTEMİ TAMAMLANDI!")
        print("=" * 60)
        print(f"📊 Toplam turnuva: {tournament_count}")
        print(f"🏆 En iyi kazanma oranı: {best_win_rate:.1%}")
        print(f"🎯 Hedef: {self.target_win_rate:.1%}")
        
        if best_win_rate >= self.target_win_rate:
            print("🎉 HEDEFE ULAŞTIK! Stockfish'i yenmeyi başardık!")
        else:
            print("😔 Hedefe ulaşamadık, daha fazla öğrenme gerekli.")
    
    def get_tournament_statistics(self) -> Dict:
        """Turnuva istatistiklerini al"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Toplam turnuva sayısı
        cursor.execute('SELECT COUNT(*) FROM tournament_results')
        total_tournaments = cursor.fetchone()[0]
        
        # Genel istatistikler
        cursor.execute('''
            SELECT 
                SUM(games_played) as total_games,
                SUM(wins) as total_wins,
                SUM(draws) as total_draws,
                SUM(losses) as total_losses,
                AVG(win_rate) as avg_win_rate,
                MAX(win_rate) as best_win_rate
            FROM tournament_results
        ''')
        
        stats = cursor.fetchone()
        total_games, total_wins, total_draws, total_losses, avg_win_rate, best_win_rate = stats
        
        # Toplam hata sayısı
        cursor.execute('SELECT COUNT(*) FROM mistakes')
        total_mistakes = cursor.fetchone()[0]
        
        # Pozisyon analizi sayısı
        cursor.execute('SELECT COUNT(*) FROM position_analyses')
        total_positions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_tournaments': total_tournaments,
            'total_games': total_games or 0,
            'total_wins': total_wins or 0,
            'total_draws': total_draws or 0,
            'total_losses': total_losses or 0,
            'avg_win_rate': avg_win_rate or 0.0,
            'best_win_rate': best_win_rate or 0.0,
            'total_mistakes': total_mistakes,
            'total_positions': total_positions,
            'cached_positions': len(self.positions_cache)
        }
    
    def close(self):
        """Sistemi kapat"""
        if self.stockfish:
            self.stockfish.quit()

def main():
    """Ana fonksiyon"""
    system = TournamentLearningSystem()
    
    try:
        # İstatistikleri göster
        stats = system.get_tournament_statistics()
        print("📊 Turnuva İstatistikleri:")
        print(f"   Toplam turnuva: {stats['total_tournaments']}")
        print(f"   Toplam oyun: {stats['total_games']}")
        print(f"   Genel kazanma oranı: {stats['avg_win_rate']:.1%}")
        print(f"   En iyi kazanma oranı: {stats['best_win_rate']:.1%}")
        print(f"   Toplam pozisyon analizi: {stats['total_positions']}")
        print(f"   Cache'deki pozisyon: {stats['cached_positions']}")
        print(f"   Toplam hata: {stats['total_mistakes']}")
        
        print("\n" + "="*60)
        
        # Turnuva sistemini başlat
        system.run_learning_tournaments()
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.close()

if __name__ == "__main__":
    main()
