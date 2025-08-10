#!/usr/bin/env python3
"""
Ultimate Stockfish Killer
Gelişmiş pozisyon analizi, sürpriz açılışlar ve hibrit motor stratejisi
"""

import chess
import chess.engine
import chess.polyglot
import chess.syzygy
import time
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionType(Enum):
    """Pozisyon tipleri"""
    OPENING = "opening"
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    ENDGAME = "endgame"
    CLOSED = "closed"
    OPEN = "open"
    CRITICAL = "critical"

class UltimateStockfishKiller:
    """Ultimate Stockfish Killer sistemi"""
    
    def __init__(self):
        self.stockfish = None
        self.book_reader = None
        self.tablebase = None
        self.move_count = 0
        self.moves_without_capture = 0
        
        # Sürpriz açılışlar (Stockfish'in zorlandığı)
        self.surprise_openings = [
            # King's Indian Defense (kapalı, manevra)
            ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "Nf3", "O-O", "Be2", "e5", "O-O", "Nc6", "d5", "Ne7"],
            
            # Modern Defense (kapalı, stratejik)
            ["e4", "g6", "d4", "Bg7", "Nc3", "d6", "f4", "Nf6", "Nf3", "O-O", "Be2", "c5", "O-O", "Nc6", "d5", "Ne5"],
            
            # Pirc Defense (kapalı, manevra)
            ["e4", "d6", "d4", "Nf6", "Nc3", "g6", "f4", "Bg7", "Nf3", "O-O", "Be2", "c5", "O-O", "Nc6", "d5", "Ne5"],
            
            # Alekhine Defense (saldırgan)
            ["e4", "Nf6", "e5", "Nd5", "d4", "d6", "Nf3", "dxe5", "Nxe5", "c6", "Be2", "Bg4", "O-O", "e6", "c4", "Nb6"],
            
            # Scandinavian Defense (saldırgan)
            ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5", "d4", "Nf6", "Nf3", "Bg4", "Be2", "e6", "O-O", "Nc6", "Be3", "O-O-O"],
            
            # Latvian Gambit (saldırgan)
            ["e4", "e5", "Nf3", "f5", "exf5", "e4", "Ne5", "Nf6", "Be2", "d6", "Nf3", "exf3", "Bxf3", "Bg4", "O-O", "Nc6"],
            
            # Elephant Gambit (saldırgan)
            ["e4", "e5", "Nf3", "d5", "exd5", "e4", "Ne5", "Nf6", "Be2", "Bg4", "O-O", "Nc6", "d3", "exd3", "Bxd3", "Bd6"],
            
            # Englund Gambit (saldırgan)
            ["d4", "e5", "dxe5", "Nc6", "Nf3", "Qe7", "Bf4", "Qb4+", "Bd2", "Qxb2", "Nc3", "Bb4", "Rb1", "Qa3", "Rb3", "Qa5"],
            
            # Budapest Gambit (saldırgan)
            ["d4", "Nf6", "c4", "e5", "dxe5", "Ng4", "Bf4", "Nc6", "Nf3", "Bb4+", "Nc3", "Qe7", "Qd5", "f5", "exf6", "Nxf6"],
            
            # Grob's Attack (saldırgan)
            ["g4", "d5", "Bg2", "Bxg4", "c4", "c6", "Qb3", "e6", "Nc3", "Nf6", "d3", "Be7", "Nf3", "O-O", "O-O", "Nbd7"],
            
            # Polish Opening (saldırgan)
            ["b4", "e5", "Bb2", "Bxb4", "Bxe5", "Nf6", "e3", "O-O", "Nf3", "d5", "Be2", "Bg4", "O-O", "Nc6", "d3", "Re8"],
            
            # Sokolsky Opening (saldırgan)
            ["b4", "e5", "Bb2", "Bxb4", "Bxe5", "Nf6", "e3", "O-O", "Nf3", "d5", "Be2", "Bg4", "O-O", "Nc6", "d3", "Re8"],
            
            # Bird's Opening (saldırgan)
            ["f4", "d5", "Nf3", "Nf6", "e3", "g6", "Be2", "Bg7", "O-O", "O-O", "d3", "c5", "Nc3", "Nc6", "Qe1", "Qc7"],
            
            # Dutch Defense (kapalı, stratejik)
            ["d4", "f5", "g3", "Nf6", "Bg2", "e6", "Nf3", "Be7", "O-O", "O-O", "c4", "d6", "Nc3", "Qe8", "Qc2", "Qh5"]
        ]
        
        self._initialize_engines()
        self._initialize_book_and_tablebase()
    
    def _initialize_engines(self):
        """Motorları başlat"""
        try:
            self.stockfish = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
            self.stockfish.configure({
                "Threads": 4,
                "Hash": 2048,
                "MultiPV": 1,
                "Contempt": 10
            })
            logger.info("Stockfish başlatıldı")
        except Exception as e:
            logger.error(f"Stockfish başlatma hatası: {e}")
    
    def _initialize_book_and_tablebase(self):
        """Kitap ve tablebase'i başlat"""
        # Tablebase
        tablebase_path = Path("data/tablebases")
        if tablebase_path.exists():
            try:
                self.tablebase = chess.syzygy.open_tablebases(str(tablebase_path))
                logger.info(f"Tablebase yüklendi: {tablebase_path}")
            except Exception as e:
                logger.warning(f"Tablebase yükleme hatası: {e}")
    
    def analyze_position(self, board: chess.Board) -> Dict:
        """Gelişmiş pozisyon analizi"""
        features = {}
        
        # Temel özellikler
        features['move_count'] = len(board.move_stack)
        features['piece_count'] = len(board.piece_map())
        features['pawn_count'] = len(board.pieces(chess.PAWN, chess.WHITE)) + len(board.pieces(chess.PAWN, chess.BLACK))
        
        # Merkez kontrolü
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        center_control = 0
        for square in center_squares:
            if board.piece_at(square):
                center_control += 1
        features['center_control'] = center_control / 4.0
        
        # Piyon yapısı karmaşıklığı
        pawn_complexity = self._analyze_pawn_structure(board)
        features['pawn_complexity'] = pawn_complexity
        
        # Taktik fırsatlar
        tactical_opportunities = self._analyze_tactical_opportunities(board)
        features['tactical_opportunities'] = tactical_opportunities
        
        # Pozisyon tipini belirle
        position_type = self._classify_position(board, features)
        features['position_type'] = position_type
        
        return features
    
    def _analyze_pawn_structure(self, board: chess.Board) -> float:
        """Piyon yapısı analizi"""
        complexity = 0.0
        
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
        
        return min(1.0, complexity)
    
    def _is_isolated_pawn(self, board: chess.Board, square: int) -> bool:
        """İzole piyon kontrolü"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        color = board.piece_at(square).color
        
        # Yan dosyalarda piyon var mı?
        for adj_file in [file - 1, file + 1]:
            if 0 <= adj_file <= 7:
                for r in range(8):
                    adj_square = chess.square(adj_file, r)
                    piece = board.piece_at(adj_square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        return False
        
        return True
    
    def _analyze_tactical_opportunities(self, board: chess.Board) -> float:
        """Taktik fırsatlar analizi"""
        opportunities = 0.0
        
        # Şah tehditleri
        if board.is_check():
            opportunities += 0.3
        
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
        
        return min(1.0, opportunities)
    
    def _classify_position(self, board: chess.Board, features: Dict) -> PositionType:
        """Pozisyon sınıflandırması"""
        move_count = features['move_count']
        
        # Açılış
        if move_count <= 8:
            return PositionType.OPENING
        
        # Endgame
        if features['piece_count'] <= 12:
            return PositionType.ENDGAME
        
        # Kapalı pozisyon (Stockfish'in zorlandığı)
        if (features['pawn_complexity'] >= 0.7 and 
            features['center_control'] <= 0.3):
            return PositionType.CLOSED
        
        # Kritik pozisyon
        if features['tactical_opportunities'] >= 0.7:
            return PositionType.CRITICAL
        
        # Taktik pozisyon
        if features['tactical_opportunities'] >= 0.5:
            return PositionType.TACTICAL
        
        # Stratejik pozisyon
        if features['pawn_complexity'] >= 0.6:
            return PositionType.STRATEGIC
        
        return PositionType.OPEN
    
    def get_surprise_opening_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Sürpriz açılış hamlesi al"""
        move_count = len(board.move_stack)
        
        if move_count >= 20:  # Sadece açılışta kullan
            return None
        
        # Mevcut pozisyona uygun sürpriz açılış seç
        for opening_moves in self.surprise_openings:
            if move_count < len(opening_moves):
                try:
                    move_san = opening_moves[move_count]
                    move = board.parse_san(move_san)
                    if move in board.legal_moves:
                        return move
                except:
                    continue
        
        return None
    
    def get_tablebase_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Tablebase'den hamle al"""
        if not self.tablebase:
            return None
        
        piece_count = len(board.piece_map())
        if piece_count > 6:  # Sadece 6 taş ve altı
            return None
        
        try:
            wdl = self.tablebase.probe_wdl(board)
            dtz = self.tablebase.probe_dtz(board)
            
            if wdl > 0:  # Kazanma pozisyonu
                # En hızlı kazanma hamlesini bul
                best_move = None
                best_dtz = float('inf')
                
                for move in board.legal_moves:
                    board.push(move)
                    try:
                        move_dtz = self.tablebase.probe_dtz(board)
                        if move_dtz < best_dtz:
                            best_dtz = move_dtz
                            best_move = move
                    except:
                        pass
                    board.pop()
                
                return best_move
            
        except Exception as e:
            logger.warning(f"Tablebase hatası: {e}")
        
        return None
    
    def get_strategic_move(self, board: chess.Board, features: Dict) -> Optional[chess.Move]:
        """Stratejik hamle al"""
        position_type = features['position_type']
        
        # Kapalı pozisyonlarda manevra stratejisi
        if position_type == PositionType.CLOSED:
            return self._get_closed_position_move(board)
        
        # Stratejik pozisyonlarda piyon yapısı odaklı
        elif position_type == PositionType.STRATEGIC:
            return self._get_strategic_position_move(board)
        
        # Kritik pozisyonlarda derin analiz
        elif position_type == PositionType.CRITICAL:
            return self._get_critical_position_move(board)
        
        return None
    
    def _get_closed_position_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Kapalı pozisyon hamlesi (Stockfish'in zorlandığı)"""
        # 1. Piyon zincirleri oluştur
        pawn_moves = []
        for move in board.legal_moves:
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.PAWN:
                pawn_moves.append(move)
        
        if pawn_moves:
            # Merkez piyon hamlelerini tercih et
            center_pawn_moves = []
            for move in pawn_moves:
                to_file = chess.square_file(move.to_square)
                to_rank = chess.square_rank(move.to_square)
                if 2 <= to_file <= 5 and to_rank >= 3:  # Merkez ve ileri
                    center_pawn_moves.append(move)
            
            if center_pawn_moves:
                return random.choice(center_pawn_moves)
            else:
                return random.choice(pawn_moves)
        
        # 2. Manevra hamleleri (at ve fil)
        maneuver_moves = []
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                # Kapalı pozisyonlarda manevra alanları
                to_file = chess.square_file(move.to_square)
                to_rank = chess.square_rank(move.to_square)
                if (1 <= to_file <= 6 and 2 <= to_rank <= 5):  # Manevra alanları
                    maneuver_moves.append(move)
        
        if maneuver_moves:
            return random.choice(maneuver_moves)
        
        # 3. Kale manevraları
        rook_moves = []
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.ROOK:
                rook_moves.append(move)
        
        if rook_moves:
            return random.choice(rook_moves)
        
        return None
    
    def _get_strategic_position_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Stratejik pozisyon hamlesi"""
        # Gelişim hamleleri
        development_moves = []
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                # Merkeze doğru hamleler
                to_file = chess.square_file(move.to_square)
                if 2 <= to_file <= 5:
                    development_moves.append(move)
        
        if development_moves:
            return random.choice(development_moves)
        
        return None
    
    def _get_critical_position_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Kritik pozisyon hamlesi"""
        # Stockfish ile derin analiz
        if self.stockfish:
            try:
                result = self.stockfish.play(board, chess.engine.Limit(time=3.0, depth=20))
                return result.move
            except Exception as e:
                logger.error(f"Stockfish analiz hatası: {e}")
        
        return None
    
    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """En iyi hamleyi al"""
        # 1. Tablebase kontrolü
        tablebase_move = self.get_tablebase_move(board)
        if tablebase_move:
            logger.info("Tablebase hamlesi kullanıldı")
            return tablebase_move
        
        # 2. Sürpriz açılış kontrolü
        surprise_move = self.get_surprise_opening_move(board)
        if surprise_move:
            logger.info("Sürpriz açılış hamlesi kullanıldı")
            return surprise_move
        
        # 3. Pozisyon analizi
        features = self.analyze_position(board)
        position_type = features['position_type']
        
        logger.info(f"Pozisyon tipi: {position_type.value}")
        
        # 4. Stratejik hamle
        strategic_move = self.get_strategic_move(board, features)
        if strategic_move:
            logger.info("Stratejik hamle kullanıldı")
            return strategic_move
        
        # 5. Stockfish fallback
        if self.stockfish:
            try:
                # Pozisyona göre zaman ayarla
                time_limit = 2.0
                if position_type == PositionType.CLOSED:
                    time_limit = 4.0  # Kapalı pozisyonlarda daha fazla zaman (Stockfish'in zorlandığı)
                elif position_type == PositionType.CRITICAL:
                    time_limit = 5.0  # Kritik pozisyonlarda daha fazla zaman
                elif position_type == PositionType.STRATEGIC:
                    time_limit = 3.5  # Stratejik pozisyonlarda orta zaman
                elif position_type == PositionType.ENDGAME:
                    time_limit = 1.5  # Endgame'de daha az zaman
                
                result = self.stockfish.play(board, chess.engine.Limit(time=time_limit))
                logger.info(f"Stockfish hamlesi kullanıldı ({time_limit}s)")
                return result.move
            except Exception as e:
                logger.error(f"Stockfish hatası: {e}")
        
        return None
    
    def play_game_against_stockfish(self, max_moves: int = 200) -> Dict:
        """Stockfish'e karşı oyun oyna"""
        board = chess.Board()
        moves = []
        position_analyses = []
        
        print("🥊 Ultimate Stockfish Killer vs Stockfish 17.1")
        print("=" * 60)
        
        while not board.is_game_over() and len(moves) < max_moves:
            move_count = len(moves) + 1
            
            if board.turn == chess.WHITE:
                # Bizim bot
                print(f"\n{move_count}. Beyaz (Ultimate Killer) düşünüyor...")
                
                # Pozisyon analizi
                features = self.analyze_position(board)
                position_analyses.append({
                    'move': move_count,
                    'position_type': features['position_type'].value,
                    'features': features
                })
                
                start_time = time.time()
                move = self.get_best_move(board)
                end_time = time.time()
                
                if move:
                    san_move = board.san(move)
                    think_time = end_time - start_time
                    
                    print(f"   {san_move} ({move.uci()}) - {features['position_type'].value} - {think_time:.2f}s")
                    
                    # 50 hamle kuralı
                    if board.is_capture(move):
                        self.moves_without_capture = 0
                    else:
                        self.moves_without_capture += 1
                    
                    board.push(move)
                    moves.append({
                        'move': move_count,
                        'color': 'white',
                        'san': san_move,
                        'uci': move.uci(),
                        'think_time': think_time,
                        'position_type': features['position_type'].value
                    })
                    
                    if self.moves_without_capture >= 100:
                        print("   50 hamle kuralı! Beraberlik")
                        break
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
                    
                    # 50 hamle kuralı
                    if board.is_capture(result.move):
                        self.moves_without_capture = 0
                    else:
                        self.moves_without_capture += 1
                    
                    board.push(result.move)
                    moves.append({
                        'move': move_count,
                        'color': 'black',
                        'san': san_move,
                        'uci': result.move.uci(),
                        'think_time': think_time,
                        'position_type': 'stockfish'
                    })
                    
                    if self.moves_without_capture >= 100:
                        print("   50 hamle kuralı! Beraberlik")
                        break
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
        
        # Oyun sonucu
        result = board.result()
        print(f"\n🏁 OYUN SONUCU: {result}")
        print(f"📊 Toplam hamle: {len(moves)}")
        
        return {
            'result': result,
            'moves': moves,
            'position_analyses': position_analyses,
            'final_fen': board.fen()
        }
    
    def close(self):
        """Sistemi kapat"""
        if self.stockfish:
            self.stockfish.quit()
        if self.tablebase:
            self.tablebase.close()

def main():
    """Ana fonksiyon"""
    killer = UltimateStockfishKiller()
    
    try:
        result = killer.play_game_against_stockfish()
        
        print(f"\n📈 Pozisyon Analizi:")
        for analysis in result['position_analyses']:
            print(f"   Hamle {analysis['move']}: {analysis['position_type']}")
        
        if result['result'] == "1-0":
            print("\n🎉 STOCKFISH'İ YENDİK!")
        elif result['result'] == "0-1":
            print("\n😔 Stockfish kazandı")
        else:
            print("\n🤝 Beraberlik")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        killer.close()

if __name__ == "__main__":
    main()
