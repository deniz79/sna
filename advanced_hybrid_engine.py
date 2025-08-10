#!/usr/bin/env python3
"""
Gelişmiş Hibrit Motor Sistemi
Pozisyon bazlı otomatik motor seçimi ve optimizasyon
"""

import chess
import chess.engine
import chess.polyglot
import chess.syzygy
import logging
import time
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum
import threading
from dataclasses import dataclass
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionType(Enum):
    """Gelişmiş pozisyon tipleri"""
    OPENING = "opening"
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    ENDGAME = "endgame"
    COMPLEX = "complex"
    SIMPLE = "simple"
    CLOSED = "closed"
    OPEN = "open"
    CRITICAL = "critical"

class EngineType(Enum):
    """Motor tipleri"""
    STOCKFISH = "stockfish"
    LCZERO = "lc0"
    CUSTOM = "custom"

@dataclass
class EngineConfig:
    """Motor konfigürasyonu"""
    name: str
    path: str
    type: EngineType
    hash_size: int = 1024
    threads: int = 4
    depth_limit: int = 20
    time_limit: float = 2.0
    contempt: int = 0
    skill_level: int = 20
    uci_options: Dict = None

@dataclass
class PositionAnalysis:
    """Pozisyon analizi sonucu"""
    position_type: PositionType
    confidence: float
    features: Dict[str, float]
    recommended_engine: EngineType
    time_allocation: float
    depth_allocation: int

class AdvancedPositionAnalyzer:
    """Gelişmiş pozisyon analiz sistemi"""
    
    def __init__(self):
        self.feature_weights = {
            'piece_count': 0.15,
            'pawn_structure': 0.20,
            'center_control': 0.15,
            'development': 0.10,
            'king_safety': 0.15,
            'tactical_opportunities': 0.25
        }
    
    def analyze_position(self, board: chess.Board) -> PositionAnalysis:
        """Kapsamlı pozisyon analizi"""
        features = self._extract_features(board)
        position_type = self._classify_position(board, features)
        confidence = self._calculate_confidence(features)
        
        # Motor önerisi
        recommended_engine = self._recommend_engine(position_type, features)
        
        # Zaman ve derinlik tahsisi
        time_allocation = self._calculate_time_allocation(position_type, features)
        depth_allocation = self._calculate_depth_allocation(position_type, features)
        
        return PositionAnalysis(
            position_type=position_type,
            confidence=confidence,
            features=features,
            recommended_engine=recommended_engine,
            time_allocation=time_allocation,
            depth_allocation=depth_allocation
        )
    
    def _extract_features(self, board: chess.Board) -> Dict[str, float]:
        """Gelişmiş özellik çıkarma"""
        features = {}
        
        # Temel özellikler
        features['piece_count'] = self._analyze_piece_count(board)
        features['pawn_structure'] = self._analyze_pawn_structure(board)
        features['center_control'] = self._analyze_center_control(board)
        features['development'] = self._analyze_development(board)
        features['king_safety'] = self._analyze_king_safety(board)
        features['tactical_opportunities'] = self._analyze_tactical_opportunities(board)
        
        # Yeni özellikler
        features['position_complexity'] = self._analyze_complexity(board)
        features['material_balance'] = self._analyze_material_balance(board)
        features['space_control'] = self._analyze_space_control(board)
        features['pawn_chain_structure'] = self._analyze_pawn_chains(board)
        
        return features
    
    def _analyze_piece_count(self, board: chess.Board) -> float:
        """Taş sayısı analizi"""
        piece_count = len(board.piece_map())
        return 1.0 - (piece_count / 32.0)  # 0 = başlangıç, 1 = endgame
    
    def _analyze_pawn_structure(self, board: chess.Board) -> float:
        """Piyon yapısı analizi"""
        pawns = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
        pawn_count = len(pawns)
        
        # Piyon zincirleri ve yapı karmaşıklığı
        complexity = 0.0
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
    
    def _analyze_center_control(self, board: chess.Board) -> float:
        """Merkez kontrolü analizi"""
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        control = 0.0
        
        for square in center_squares:
            if board.piece_at(square):
                control += 0.25
        
        return control
    
    def _analyze_development(self, board: chess.Board) -> float:
        """Gelişim analizi"""
        move_count = len(board.move_stack)
        return min(1.0, move_count / 20.0)
    
    def _analyze_king_safety(self, board: chess.Board) -> float:
        """Şah güvenliği analizi"""
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        safety = 0.0
        
        if white_king:
            # Şahın merkeze yakınlığı
            file = chess.square_file(white_king)
            if 2 <= file <= 5:
                safety += 0.5
        
        if black_king:
            file = chess.square_file(black_king)
            if 2 <= file <= 5:
                safety += 0.5
        
        return safety
    
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
                # At fork fırsatları
                opportunities += 0.1
        
        # Pin fırsatları
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type in [chess.ROOK, chess.BISHOP, chess.QUEEN]:
                opportunities += 0.05
        
        return min(1.0, opportunities)
    
    def _analyze_complexity(self, board: chess.Board) -> float:
        """Pozisyon karmaşıklığı"""
        # Legal hamle sayısı
        legal_moves = len(list(board.legal_moves))
        complexity = legal_moves / 50.0  # Normalize
        
        # Taş aktivitesi
        piece_activity = 0.0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                piece_activity += 1
        
        return min(1.0, (complexity + piece_activity / 32.0) / 2.0)
    
    def _analyze_material_balance(self, board: chess.Board) -> float:
        """Materyal dengesi"""
        white_material = 0
        black_material = 0
        
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        balance = abs(white_material - black_material) / 39.0  # Maksimum fark
        return balance
    
    def _analyze_space_control(self, board: chess.Board) -> float:
        """Alan kontrolü"""
        control = 0.0
        
        # Merkez alanları
        center_area = [chess.C3, chess.D3, chess.E3, chess.F3,
                      chess.C4, chess.D4, chess.E4, chess.F4,
                      chess.C5, chess.D5, chess.E5, chess.F5,
                      chess.C6, chess.D6, chess.E6, chess.F6]
        
        for square in center_area:
            if board.piece_at(square):
                control += 0.0625  # 1/16
        
        return control
    
    def _analyze_pawn_chains(self, board: chess.Board) -> float:
        """Piyon zincirleri analizi"""
        chains = 0.0
        
        for color in [chess.WHITE, chess.BLACK]:
            pawns = board.pieces(chess.PAWN, color)
            for square in pawns:
                # Piyon zinciri uzunluğu
                chain_length = self._get_pawn_chain_length(board, square, color)
                chains += chain_length / 8.0
        
        return min(1.0, chains)
    
    def _get_pawn_chain_length(self, board: chess.Board, square: int, color: bool) -> int:
        """Piyon zinciri uzunluğunu hesapla"""
        length = 1
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        # İleri doğru zincir
        for r in range(rank + 1, 8):
            new_square = chess.square(file, r)
            if board.piece_at(new_square) == chess.Piece(chess.PAWN, color):
                length += 1
            else:
                break
        
        return length
    
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
    
    def _classify_position(self, board: chess.Board, features: Dict[str, float]) -> PositionType:
        """Gelişmiş pozisyon sınıflandırması"""
        move_count = len(board.move_stack)
        
        # Açılış
        if move_count <= 8:
            return PositionType.OPENING
        
        # Endgame
        if features['piece_count'] >= 0.8:
            return PositionType.ENDGAME
        
        # Kapalı pozisyon
        if (features['pawn_structure'] >= 0.7 and 
            features['center_control'] <= 0.3 and
            features['position_complexity'] >= 0.6):
            return PositionType.CLOSED
        
        # Kritik pozisyon
        if (features['tactical_opportunities'] >= 0.7 or
            features['material_balance'] >= 0.5):
            return PositionType.CRITICAL
        
        # Taktik pozisyon
        if features['tactical_opportunities'] >= 0.5:
            return PositionType.TACTICAL
        
        # Stratejik pozisyon
        if (features['pawn_structure'] >= 0.6 and 
            features['space_control'] >= 0.5):
            return PositionType.STRATEGIC
        
        # Karmaşık pozisyon
        if features['position_complexity'] >= 0.7:
            return PositionType.COMPLEX
        
        # Açık pozisyon
        if features['center_control'] >= 0.5:
            return PositionType.OPEN
        
        return PositionType.SIMPLE
    
    def _recommend_engine(self, position_type: PositionType, features: Dict[str, float]) -> EngineType:
        """Pozisyona göre motor önerisi"""
        if position_type == PositionType.TACTICAL:
            return EngineType.STOCKFISH
        elif position_type == PositionType.STRATEGIC:
            return EngineType.LCZERO
        elif position_type == PositionType.CLOSED:
            return EngineType.LCZERO
        elif position_type == PositionType.CRITICAL:
            return EngineType.STOCKFISH
        elif position_type == PositionType.ENDGAME:
            return EngineType.STOCKFISH
        else:
            return EngineType.STOCKFISH
    
    def _calculate_time_allocation(self, position_type: PositionType, features: Dict[str, float]) -> float:
        """Pozisyona göre zaman tahsisi"""
        base_time = 2.0
        
        # Karmaşıklığa göre artır
        if features['position_complexity'] >= 0.7:
            base_time *= 1.5
        
        # Kritik pozisyonlarda daha fazla zaman
        if position_type == PositionType.CRITICAL:
            base_time *= 2.0
        
        # Endgame'de daha az zaman
        if position_type == PositionType.ENDGAME:
            base_time *= 0.7
        
        return base_time
    
    def _calculate_depth_allocation(self, position_type: PositionType, features: Dict[str, float]) -> int:
        """Pozisyona göre derinlik tahsisi"""
        base_depth = 20
        
        # Karmaşıklığa göre artır
        if features['position_complexity'] >= 0.7:
            base_depth += 10
        
        # Kritik pozisyonlarda daha derin
        if position_type == PositionType.CRITICAL:
            base_depth += 15
        
        # Endgame'de daha derin
        if position_type == PositionType.ENDGAME:
            base_depth += 5
        
        return base_depth
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Analiz güven skorunu hesapla"""
        confidence = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in features:
                confidence += features[feature] * weight
        
        return min(1.0, confidence)

class AdvancedEngineManager:
    """Gelişmiş motor yöneticisi"""
    
    def __init__(self, configs: List[EngineConfig]):
        self.configs = {config.name: config for config in configs}
        self.engines = {}
        self.performance_history = {}
        self.lock = threading.Lock()
        
        # Motorları başlat
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Motorları başlat"""
        for name, config in self.configs.items():
            try:
                engine = chess.engine.SimpleEngine.popen_uci(config.path)
                
                # UCI seçeneklerini ayarla
                uci_options = {
                    "Threads": config.threads,
                    "Hash": config.hash_size,
                    "MultiPV": 1
                }
                
                if config.uci_options:
                    uci_options.update(config.uci_options)
                
                engine.configure(uci_options)
                self.engines[name] = engine
                
                # Performans geçmişini başlat
                self.performance_history[name] = {
                    'wins': 0, 'losses': 0, 'draws': 0,
                    'avg_time': 0.0, 'avg_depth': 0.0
                }
                
                logger.info(f"Motor başlatıldı: {name}")
                
            except Exception as e:
                logger.error(f"Motor başlatma hatası {name}: {e}")
    
    def get_engine(self, engine_type: EngineType) -> Optional[chess.engine.SimpleEngine]:
        """Motor tipine göre motor al"""
        for name, config in self.configs.items():
            if config.type == engine_type:
                return self.engines.get(name)
        return None
    
    def get_best_move(self, board: chess.Board, analysis: PositionAnalysis) -> Tuple[chess.Move, Dict]:
        """En iyi hamleyi al"""
        with self.lock:
            engine = self.get_engine(analysis.recommended_engine)
            
            if not engine:
                # Fallback: Stockfish
                engine = self.get_engine(EngineType.STOCKFISH)
            
            if not engine:
                return None, {}
            
            # Zaman ve derinlik limitleri
            limit = chess.engine.Limit(
                time=analysis.time_allocation,
                depth=analysis.depth_allocation
            )
            
            try:
                result = engine.play(board, limit)
                
                # Performans kaydet
                self._update_performance(analysis.recommended_engine, result)
                
                return result.move, {
                    'engine': analysis.recommended_engine.value,
                    'time_used': result.info.get('time', 0),
                    'depth_reached': result.info.get('depth', 0),
                    'nodes_searched': result.info.get('nodes', 0)
                }
                
            except Exception as e:
                logger.error(f"Motor hatası: {e}")
                return None, {}
    
    def _update_performance(self, engine_type: EngineType, result):
        """Performans güncelle"""
        engine_name = None
        for name, config in self.configs.items():
            if config.type == engine_type:
                engine_name = name
                break
        
        if engine_name:
            history = self.performance_history[engine_name]
            history['avg_time'] = (history['avg_time'] + result.info.get('time', 0)) / 2
            history['avg_depth'] = (history['avg_depth'] + result.info.get('depth', 0)) / 2
    
    def close(self):
        """Motorları kapat"""
        for engine in self.engines.values():
            try:
                engine.quit()
            except:
                pass
        self.engines.clear()

class AdvancedHybridEngine:
    """Gelişmiş hibrit motor sistemi"""
    
    def __init__(self, config_path: str = "config.py"):
        self.analyzer = AdvancedPositionAnalyzer()
        self.engine_manager = None
        self.book_reader = None
        self.tablebase = None
        self.learning_data = []
        
        # Konfigürasyonu yükle
        self._load_config(config_path)
        
        # Motor yöneticisini başlat
        self._initialize_engines()
        
        # Kitap ve tablebase'i başlat
        self._initialize_book_and_tablebase()
    
    def _load_config(self, config_path: str):
        """Konfigürasyonu yükle"""
        import config
        self.config = config
    
    def _initialize_engines(self):
        """Motorları başlat"""
        configs = []
        
        # Stockfish
        stockfish_config = EngineConfig(
            name="stockfish",
            path=self.config.ENGINES["stockfish"]["path"],
            type=EngineType.STOCKFISH,
            hash_size=2048,
            threads=psutil.cpu_count(),
            depth_limit=30,
            time_limit=3.0,
            contempt=10
        )
        configs.append(stockfish_config)
        
        # LCZero (eğer varsa)
        if "lc0" in self.config.ENGINES:
            lc0_config = EngineConfig(
                name="lc0",
                path=self.config.ENGINES["lc0"]["path"],
                type=EngineType.LCZERO,
                hash_size=1024,
                threads=2,
                depth_limit=20,
                time_limit=2.0
            )
            configs.append(lc0_config)
        
        self.engine_manager = AdvancedEngineManager(configs)
    
    def _initialize_book_and_tablebase(self):
        """Kitap ve tablebase'i başlat"""
        # Açılış kitabı
        book_path = Path("data/books/aggressive_anti_stockfish.bin")
        if book_path.exists():
            try:
                self.book_reader = chess.polyglot.open_reader(book_path)
                logger.info(f"Açılış kitabı yüklendi: {book_path}")
            except Exception as e:
                logger.warning(f"Kitap yükleme hatası: {e}")
        
        # Tablebase
        tablebase_path = Path("data/tablebases")
        if tablebase_path.exists():
            try:
                self.tablebase = chess.syzygy.open_tablebases(str(tablebase_path))
                logger.info(f"Tablebase yüklendi: {tablebase_path}")
            except Exception as e:
                logger.warning(f"Tablebase yükleme hatası: {e}")
    
    def get_move(self, board: chess.Board, time_limit: float = 2.0) -> Optional[chess.Move]:
        """En iyi hamleyi al"""
        # 1. Tablebase kontrolü
        if self.tablebase and self._should_use_tablebase(board):
            move = self._get_tablebase_move(board)
            if move:
                return move
        
        # 2. Açılış kitabı kontrolü
        if self.book_reader and self._should_use_book(board):
            move = self._get_book_move(board)
            if move:
                return move
        
        # 3. Pozisyon analizi
        analysis = self.analyzer.analyze_position(board)
        
        # 4. Motor seçimi ve hamle
        move, info = self.engine_manager.get_best_move(board, analysis)
        
        # 5. Öğrenme verisi kaydet
        self._save_learning_data(board, analysis, move, info)
        
        return move
    
    def _should_use_tablebase(self, board: chess.Board) -> bool:
        """Tablebase kullanılmalı mı?"""
        if not self.tablebase:
            return False
        
        piece_count = len(board.piece_map())
        return piece_count <= 6
    
    def _get_tablebase_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Tablebase'den hamle al"""
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
    
    def _should_use_book(self, board: chess.Board) -> bool:
        """Kitap kullanılmalı mı?"""
        if not self.book_reader:
            return False
        
        move_count = len(board.move_stack)
        return move_count <= 15  # İlk 15 hamle
    
    def _get_book_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Kitaptan hamle al"""
        try:
            entry = self.book_reader.weighted_choice(board)
            return entry.move
        except Exception as e:
            logger.warning(f"Kitap hatası: {e}")
            return None
    
    def _save_learning_data(self, board: chess.Board, analysis: PositionAnalysis, 
                           move: chess.Move, info: Dict):
        """Öğrenme verisi kaydet"""
        data = {
            'fen': board.fen(),
            'position_type': analysis.position_type.value,
            'features': analysis.features,
            'recommended_engine': analysis.recommended_engine.value,
            'move': move.uci() if move else None,
            'time_used': info.get('time_used', 0),
            'depth_reached': info.get('depth_reached', 0),
            'timestamp': time.time()
        }
        
        self.learning_data.append(data)
        
        # Veriyi dosyaya kaydet (her 100 hamlede bir)
        if len(self.learning_data) % 100 == 0:
            self._save_learning_data_to_file()
    
    def _save_learning_data_to_file(self):
        """Öğrenme verisini dosyaya kaydet"""
        data_file = Path("data/learning_data.json")
        data_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(data_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
            logger.info(f"Öğrenme verisi kaydedildi: {data_file}")
        except Exception as e:
            logger.error(f"Veri kaydetme hatası: {e}")
    
    def get_performance_stats(self) -> Dict:
        """Performans istatistiklerini al"""
        return {
            'engine_performance': self.engine_manager.performance_history,
            'learning_data_count': len(self.learning_data),
            'position_type_distribution': self._get_position_type_distribution()
        }
    
    def _get_position_type_distribution(self) -> Dict:
        """Pozisyon tipi dağılımını hesapla"""
        distribution = {}
        for data in self.learning_data:
            pos_type = data['position_type']
            distribution[pos_type] = distribution.get(pos_type, 0) + 1
        return distribution
    
    def close(self):
        """Sistemi kapat"""
        if self.engine_manager:
            self.engine_manager.close()
        if self.book_reader:
            self.book_reader.close()
        if self.tablebase:
            self.tablebase.close()

def main():
    """Test fonksiyonu"""
    engine = AdvancedHybridEngine()
    
    # Test pozisyonu
    board = chess.Board()
    
    print("🎯 Gelişmiş Hibrit Motor Testi")
    print("=" * 50)
    
    # İlk hamle
    move = engine.get_move(board)
    if move:
        print(f"İlk hamle: {board.san(move)}")
        board.push(move)
        
        # Analiz
        analysis = engine.analyzer.analyze_position(board)
        print(f"Pozisyon tipi: {analysis.position_type.value}")
        print(f"Önerilen motor: {analysis.recommended_engine.value}")
        print(f"Zaman tahsisi: {analysis.time_allocation:.2f}s")
        print(f"Derinlik tahsisi: {analysis.depth_allocation}")
    
    # İstatistikler
    stats = engine.get_performance_stats()
    print(f"\nPerformans: {stats}")
    
    engine.close()

if __name__ == "__main__":
    main()
