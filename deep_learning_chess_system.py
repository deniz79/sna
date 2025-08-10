#!/usr/bin/env python3
"""
Derin Düşünce ve Öğrenme Satranç Sistemi
Tüm olasılıkları analiz eder, hataları kaydeder ve tekrarlamaz
"""

import chess
import chess.engine
import chess.pgn
import json
import sqlite3
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PositionAnalysis:
    """Pozisyon analizi verisi"""
    fen: str
    position_hash: str
    move_count: int
    piece_count: int
    pawn_structure: str
    tactical_opportunities: float
    strategic_complexity: float
    position_type: str
    evaluation: float
    best_moves: List[Tuple[str, float]]
    timestamp: datetime

@dataclass
class GameResult:
    """Oyun sonucu verisi"""
    game_id: str
    result: str
    moves: List[Dict]
    position_analyses: List[PositionAnalysis]
    mistakes: List[Dict]
    learning_insights: List[str]
    timestamp: datetime

class DeepLearningChessSystem:
    """Derin düşünce ve öğrenme satranç sistemi"""
    
    def __init__(self):
        self.stockfish = None
        self.database_path = Path("data/learning_database.db")
        self.positions_cache = {}
        self.mistakes_database = {}
        self.learning_history = []
        
        # Derin analiz parametreleri
        self.analysis_depth = 25
        self.analysis_time = 10.0
        self.max_variations = 5
        
        self._initialize_engine()
        self._initialize_database()
        self._load_learning_data()
    
    def _initialize_engine(self):
        """Stockfish motorunu başlat"""
        try:
            self.stockfish = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
            self.stockfish.configure({
                "Threads": 8,  # Daha fazla thread
                "Hash": 4096,  # Daha büyük hash
                "MultiPV": self.max_variations,
                "Contempt": 0  # Tarafsız değerlendirme
            })
            logger.info("Stockfish derin analiz modunda başlatıldı")
        except Exception as e:
            logger.error(f"Stockfish başlatma hatası: {e}")
    
    def _initialize_database(self):
        """Öğrenme veritabanını başlat"""
        self.database_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Pozisyon analizi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_hash TEXT UNIQUE,
                fen TEXT,
                move_count INTEGER,
                piece_count INTEGER,
                pawn_structure TEXT,
                tactical_opportunities REAL,
                strategic_complexity REAL,
                position_type TEXT,
                evaluation REAL,
                best_moves TEXT,
                timestamp DATETIME,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            )
        ''')
        
        # Oyun sonuçları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT UNIQUE,
                result TEXT,
                moves TEXT,
                position_analyses TEXT,
                mistakes TEXT,
                learning_insights TEXT,
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
                timestamp DATETIME
            )
        ''')
        
        # Öğrenme geçmişi tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_hash TEXT,
                lesson_learned TEXT,
                improvement_type TEXT,
                confidence REAL,
                timestamp DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Öğrenme veritabanı başlatıldı")
    
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
    
    def _analyze_pawn_structure(self, board: chess.Board) -> str:
        """Piyon yapısını analiz et"""
        structure = []
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = list(board.pieces(chess.PAWN, color))
            pawns.sort()
            structure.append(f"{'w' if color else 'b'}:{','.join(map(str, pawns))}")
        
        return "|".join(structure)
    
    def _calculate_tactical_opportunities(self, board: chess.Board) -> float:
        """Taktik fırsatları hesapla"""
        opportunities = 0.0
        
        # Şah tehditleri
        if board.is_check():
            opportunities += 0.5
        
        # Fork fırsatları
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.KNIGHT:
                opportunities += 0.1
        
        # Pin fırsatları
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type in [chess.ROOK, chess.BISHOP, chess.QUEEN]:
                opportunities += 0.05
        
        # Skewer fırsatları
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type in [chess.ROOK, chess.QUEEN]:
                opportunities += 0.03
        
        return min(1.0, opportunities)
    
    def _calculate_strategic_complexity(self, board: chess.Board) -> float:
        """Stratejik karmaşıklığı hesapla"""
        complexity = 0.0
        
        # Piyon yapısı karmaşıklığı
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            for square in pawns:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                
                # Merkez piyonları
                if 2 <= file <= 5 and 2 <= rank <= 5:
                    complexity += 0.1
                
                # İzole piyonlar
                if self._is_isolated_pawn(board, square):
                    complexity += 0.2
                
                # Çifte piyonlar
                if self._is_doubled_pawn(board, square):
                    complexity += 0.15
        
        # Merkez kontrolü
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        center_control = sum(1 for square in center_squares if board.piece_at(square))
        complexity += center_control * 0.1
        
        # Gelişim durumu
        developed_pieces = 0
        for piece_type in [chess.KNIGHT, chess.BISHOP]:
            for color in [chess.WHITE, chess.BLACK]:
                pieces = board.pieces(piece_type, color)
                for square in pieces:
                    if self._is_developed_piece(board, square, color):
                        developed_pieces += 1
        
        complexity += developed_pieces * 0.05
        
        return min(1.0, complexity)
    
    def _is_isolated_pawn(self, board: chess.Board, square: int) -> bool:
        """İzole piyon kontrolü"""
        file = chess.square_file(square)
        color = board.piece_at(square).color
        
        for adj_file in [file - 1, file + 1]:
            if 0 <= adj_file <= 7:
                for r in range(8):
                    adj_square = chess.square(adj_file, r)
                    piece = board.piece_at(adj_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        return False
        return True
    
    def _is_doubled_pawn(self, board: chess.Board, square: int) -> bool:
        """Çifte piyon kontrolü"""
        file = chess.square_file(square)
        color = board.piece_at(square).color
        pawn_count = 0
        
        for r in range(8):
            check_square = chess.square(file, r)
            piece = board.piece_at(check_square)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                pawn_count += 1
        
        return pawn_count > 1
    
    def _is_developed_piece(self, board: chess.Board, square: int, color: bool) -> bool:
        """Gelişmiş taş kontrolü"""
        rank = chess.square_rank(square)
        if color == chess.WHITE:
            return rank > 1  # Beyaz için 2. sıradan ileri
        else:
            return rank < 6  # Siyah için 6. sıradan geri
    
    def _classify_position_type(self, board: chess.Board, tactical: float, strategic: float) -> str:
        """Pozisyon tipini sınıflandır"""
        move_count = len(board.move_stack)
        piece_count = len(board.piece_map())
        
        if move_count <= 10:
            return "opening"
        elif piece_count <= 12:
            return "endgame"
        elif tactical >= 0.7:
            return "tactical"
        elif strategic >= 0.7:
            return "strategic"
        elif tactical >= 0.5:
            return "tactical_strategic"
        elif strategic >= 0.5:
            return "strategic_maneuvering"
        else:
            return "quiet"
    
    def deep_position_analysis(self, board: chess.Board) -> PositionAnalysis:
        """Derin pozisyon analizi"""
        position_hash = self._get_position_hash(board)
        
        # Cache'den kontrol et
        if position_hash in self.positions_cache:
            cached_data = self.positions_cache[position_hash]
            logger.info(f"Cache'den pozisyon analizi yüklendi: {position_hash}")
            return PositionAnalysis(
                fen=board.fen(),
                position_hash=position_hash,
                move_count=len(board.move_stack),
                piece_count=len(board.piece_map()),
                pawn_structure=self._analyze_pawn_structure(board),
                tactical_opportunities=self._calculate_tactical_opportunities(board),
                strategic_complexity=self._calculate_strategic_complexity(board),
                position_type=self._classify_position_type(board, 0, 0),
                evaluation=cached_data['evaluation'],
                best_moves=cached_data['best_moves'],
                timestamp=datetime.now()
            )
        
        logger.info(f"Derin pozisyon analizi başlatılıyor: {position_hash}")
        
        # Stockfish ile derin analiz
        if self.stockfish:
            try:
                # Çoklu varyant analizi
                result = self.stockfish.analyse(
                    board, 
                    chess.engine.Limit(depth=self.analysis_depth, time=self.analysis_time),
                    multipv=self.max_variations
                )
                
                # En iyi hamleleri çıkar
                best_moves = []
                for i, analysis in enumerate(result):
                    if i < self.max_variations:
                        move_san = board.san(analysis['pv'][0]) if analysis['pv'] else "N/A"
                        score = analysis['score'].relative.score(mate_score=10000) / 100.0
                        best_moves.append((move_san, score))
                
                # Ana değerlendirme
                main_evaluation = result[0]['score'].relative.score(mate_score=10000) / 100.0
                
                # Pozisyon özellikleri
                tactical_opportunities = self._calculate_tactical_opportunities(board)
                strategic_complexity = self._calculate_strategic_complexity(board)
                position_type = self._classify_position_type(board, tactical_opportunities, strategic_complexity)
                
                analysis = PositionAnalysis(
                    fen=board.fen(),
                    position_hash=position_hash,
                    move_count=len(board.move_stack),
                    piece_count=len(board.piece_map()),
                    pawn_structure=self._analyze_pawn_structure(board),
                    tactical_opportunities=tactical_opportunities,
                    strategic_complexity=strategic_complexity,
                    position_type=position_type,
                    evaluation=main_evaluation,
                    best_moves=best_moves,
                    timestamp=datetime.now()
                )
                
                # Cache'e kaydet
                self.positions_cache[position_hash] = {
                    'fen': board.fen(),
                    'evaluation': main_evaluation,
                    'best_moves': best_moves
                }
                
                # Veritabanına kaydet
                self._save_position_analysis(analysis)
                
                logger.info(f"Derin analiz tamamlandı: {position_type} pozisyonu, değerlendirme: {main_evaluation:.2f}")
                return analysis
                
            except Exception as e:
                logger.error(f"Derin analiz hatası: {e}")
        
        # Fallback analiz
        return PositionAnalysis(
            fen=board.fen(),
            position_hash=position_hash,
            move_count=len(board.move_stack),
            piece_count=len(board.piece_map()),
            pawn_structure=self._analyze_pawn_structure(board),
            tactical_opportunities=self._calculate_tactical_opportunities(board),
            strategic_complexity=self._calculate_strategic_complexity(board),
            position_type="unknown",
            evaluation=0.0,
            best_moves=[],
            timestamp=datetime.now()
        )
    
    def _save_position_analysis(self, analysis: PositionAnalysis):
        """Pozisyon analizini veritabanına kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO position_analyses 
            (position_hash, fen, move_count, piece_count, pawn_structure, 
             tactical_opportunities, strategic_complexity, position_type, 
             evaluation, best_moves, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis.position_hash,
            analysis.fen,
            analysis.move_count,
            analysis.piece_count,
            analysis.pawn_structure,
            analysis.tactical_opportunities,
            analysis.strategic_complexity,
            analysis.position_type,
            analysis.evaluation,
            json.dumps(analysis.best_moves),
            analysis.timestamp.isoformat()
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
            logger.info(f"Bu pozisyonda {len(mistakes)} önceki hata bulundu")
            
            # Hatalı hamleleri filtrele
            bad_moves = set()
            for mistake in mistakes:
                bad_moves.add(mistake['move_played'])
            
            # En iyi hamleleri filtrele
            filtered_moves = []
            for move_san, score in analysis.best_moves:
                if move_san not in bad_moves:
                    filtered_moves.append((move_san, score))
            
            if filtered_moves:
                analysis.best_moves = filtered_moves
                logger.info("Hatalı hamleler filtrelendi")
        
        # En iyi hamleyi seç
        if analysis.best_moves:
            best_move_san = analysis.best_moves[0][0]
            try:
                best_move = board.parse_san(best_move_san)
                logger.info(f"En iyi hamle seçildi: {best_move_san} (değerlendirme: {analysis.best_moves[0][1]:.2f})")
                return best_move
            except:
                logger.warning(f"Hamle parse edilemedi: {best_move_san}")
        
        # Fallback: rastgele yasal hamle
        legal_moves = list(board.legal_moves)
        if legal_moves:
            fallback_move = legal_moves[0]
            logger.warning(f"Fallback hamle kullanıldı: {board.san(fallback_move)}")
            return fallback_move
        
        return None
    
    def record_mistake(self, board: chess.Board, move_played: chess.Move, 
                      move_evaluation: float, best_move: chess.Move, 
                      best_evaluation: float):
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
             best_evaluation, mistake_type, severity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position_hash,
            move_san,
            move_evaluation,
            best_move_san,
            best_evaluation,
            mistake_type,
            severity,
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
        
        logger.info(f"Hata kaydedildi: {mistake_type} - {move_san} yerine {best_move_san} (fark: {evaluation_diff:.2f})")
    
    def play_learning_game(self, max_moves: int = 200) -> GameResult:
        """Öğrenme oyunu oyna"""
        board = chess.Board()
        moves = []
        position_analyses = []
        mistakes = []
        learning_insights = []
        
        print("🧠 Derin Düşünce ve Öğrenme Sistemi vs Stockfish 17.1")
        print("=" * 70)
        print("💡 Sistem: Tüm olasılıkları analiz ediyor, hataları öğreniyor...")
        
        game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        while not board.is_game_over() and len(moves) < max_moves:
            move_count = len(moves) + 1
            
            if board.turn == chess.WHITE:
                # Bizim bot (derin düşünce)
                print(f"\n{move_count}. Beyaz (Derin Düşünce) düşünüyor...")
                print("   🔍 Pozisyon analiz ediliyor...")
                
                # Derin pozisyon analizi
                start_analysis = time.time()
                analysis = self.deep_position_analysis(board)
                analysis_time = time.time() - start_analysis
                
                position_analyses.append(analysis)
                
                print(f"   📊 Pozisyon tipi: {analysis.position_type}")
                print(f"   🎯 Değerlendirme: {analysis.evaluation:.2f}")
                print(f"   ⚡ Taktik fırsatlar: {analysis.tactical_opportunities:.2f}")
                print(f"   🧩 Stratejik karmaşıklık: {analysis.strategic_complexity:.2f}")
                
                # En iyi hamleleri göster
                print("   🏆 En iyi hamleler:")
                for i, (move_san, score) in enumerate(analysis.best_moves[:3]):
                    print(f"      {i+1}. {move_san} ({score:.2f})")
                
                # Hamle seçimi
                start_move = time.time()
                move = self.get_best_move_with_learning(board)
                move_time = time.time() - start_move
                
                if move:
                    san_move = board.san(move)
                    total_time = analysis_time + move_time
                    
                    print(f"   ✅ Hamle: {san_move} ({move.uci()})")
                    print(f"   ⏱️  Analiz: {analysis_time:.2f}s, Hamle: {move_time:.2f}s, Toplam: {total_time:.2f}s")
                    
                    # Hamle kalitesini kontrol et
                    move_evaluation = None
                    for move_san, score in analysis.best_moves:
                        if move_san == san_move:
                            move_evaluation = score
                            break
                    
                    if move_evaluation is not None and analysis.best_moves:
                        best_evaluation = analysis.best_moves[0][1]
                        if move_evaluation < best_evaluation - 0.1:
                            # Hata kaydet
                            self.record_mistake(board, move, move_evaluation, 
                                              board.parse_san(analysis.best_moves[0][0]), best_evaluation)
                            mistakes.append({
                                'move': move_count,
                                'move_played': san_move,
                                'move_evaluation': move_evaluation,
                                'best_move': analysis.best_moves[0][0],
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
                        'position_type': analysis.position_type,
                        'evaluation': move_evaluation
                    })
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
                    
                    print(f"   {san_move} ({result.move.uci()}) - Stockfish - {think_time:.2f}s")
                    
                    board.push(result.move)
                    moves.append({
                        'move': move_count,
                        'color': 'black',
                        'san': san_move,
                        'uci': result.move.uci(),
                        'think_time': think_time,
                        'position_type': 'stockfish'
                    })
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
        
        # Oyun sonucu
        result = board.result()
        print(f"\n🏁 OYUN SONUCU: {result}")
        print(f"📊 Toplam hamle: {len(moves)}")
        print(f"📈 Pozisyon analizi: {len(position_analyses)}")
        print(f"⚠️  Tespit edilen hatalar: {len(mistakes)}")
        
        # Öğrenme içgörüleri
        if mistakes:
            print(f"\n🎓 Öğrenme İçgörüleri:")
            for mistake in mistakes:
                insight = f"Hamle {mistake['move']}: {mistake['move_played']} yerine {mistake['best_move']} oynanmalı"
                learning_insights.append(insight)
                print(f"   • {insight}")
        
        # Oyun sonucunu kaydet
        game_result = GameResult(
            game_id=game_id,
            result=result,
            moves=moves,
            position_analyses=position_analyses,
            mistakes=mistakes,
            learning_insights=learning_insights,
            timestamp=datetime.now()
        )
        
        self._save_game_result(game_result)
        
        return game_result
    
    def _save_game_result(self, game_result: GameResult):
        """Oyun sonucunu kaydet"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO game_results 
            (game_id, result, moves, position_analyses, mistakes, learning_insights, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            game_result.game_id,
            game_result.result,
            json.dumps(game_result.moves),
            pickle.dumps(game_result.position_analyses),
            json.dumps(game_result.mistakes),
            json.dumps(game_result.learning_insights),
            game_result.timestamp.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Oyun sonucu kaydedildi: {game_result.game_id}")
    
    def get_learning_statistics(self) -> Dict:
        """Öğrenme istatistiklerini al"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Toplam oyun sayısı
        cursor.execute('SELECT COUNT(*) FROM game_results')
        total_games = cursor.fetchone()[0]
        
        # Kazanma oranı
        cursor.execute('SELECT result, COUNT(*) FROM game_results GROUP BY result')
        results = dict(cursor.fetchall())
        
        # Toplam hata sayısı
        cursor.execute('SELECT COUNT(*) FROM mistakes')
        total_mistakes = cursor.fetchone()[0]
        
        # Hata tipleri
        cursor.execute('SELECT mistake_type, COUNT(*) FROM mistakes GROUP BY mistake_type')
        mistake_types = dict(cursor.fetchall())
        
        # Pozisyon analizi sayısı
        cursor.execute('SELECT COUNT(*) FROM position_analyses')
        total_positions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_games': total_games,
            'results': results,
            'total_mistakes': total_mistakes,
            'mistake_types': mistake_types,
            'total_positions': total_positions,
            'cached_positions': len(self.positions_cache)
        }
    
    def close(self):
        """Sistemi kapat"""
        if self.stockfish:
            self.stockfish.quit()

def main():
    """Ana fonksiyon"""
    system = DeepLearningChessSystem()
    
    try:
        # İstatistikleri göster
        stats = system.get_learning_statistics()
        print("📊 Öğrenme İstatistikleri:")
        print(f"   Toplam oyun: {stats['total_games']}")
        print(f"   Toplam pozisyon analizi: {stats['total_positions']}")
        print(f"   Cache'deki pozisyon: {stats['cached_positions']}")
        print(f"   Toplam hata: {stats['total_mistakes']}")
        if stats['mistake_types']:
            print("   Hata tipleri:")
            for mistake_type, count in stats['mistake_types'].items():
                print(f"     {mistake_type}: {count}")
        
        print("\n" + "="*70)
        
        # Öğrenme oyunu oyna
        result = system.play_learning_game()
        
        if result.result == "1-0":
            print("\n🎉 STOCKFISH'İ YENDİK!")
        elif result.result == "0-1":
            print("\n😔 Stockfish kazandı")
        else:
            print("\n🤝 Beraberlik")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        system.close()

if __name__ == "__main__":
    main()
