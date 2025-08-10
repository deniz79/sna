"""
Hibrit Motor Sistemi - Pozisyon analizi ile motor seçimi
"""

import chess
import chess.engine
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from pathlib import Path

import config
from engine_wrapper import EngineWrapper

logger = logging.getLogger(__name__)

class PositionType(Enum):
    """Pozisyon tipleri"""
    OPENING = "opening"
    TACTICAL = "tactical"
    STRATEGIC = "strategic"
    ENDGAME = "endgame"
    COMPLEX = "complex"
    SIMPLE = "simple"

class EngineType(Enum):
    """Motor tipleri"""
    STOCKFISH = "stockfish"
    LCZERO = "lc0"
    CUSTOM = "custom"

class HybridEngineController:
    """Hibrit motor kontrol sistemi"""
    
    def __init__(self):
        self.engines = {}
        self.position_analyzer = PositionAnalyzer()
        self.engine_selector = EngineSelector()
        self.decision_history = []
        
        # Motorları başlat
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Tüm motorları başlat"""
        available_engines = ["stockfish", "lc0"]
        
        for engine_name in available_engines:
            try:
                engine_path = config.get_engine_path(engine_name)
                if engine_path and Path(engine_path).exists():
                    self.engines[engine_name] = EngineWrapper(engine_name)
                    logger.info(f"Motor başlatıldı: {engine_name}")
                else:
                    logger.warning(f"Motor bulunamadı: {engine_name}")
            except Exception as e:
                logger.error(f"Motor başlatma hatası {engine_name}: {e}")
    
    def get_best_move(self, board: chess.Board, time_limit: float = None) -> Optional[chess.Move]:
        """En uygun motoru seç ve hamle al"""
        try:
            # Pozisyonu analiz et
            position_info = self.position_analyzer.analyze_position(board)
            
            # En uygun motoru seç
            selected_engine = self.engine_selector.select_engine(
                position_info, 
                available_engines=list(self.engines.keys())
            )
            
            # Hamleyi al
            if selected_engine in self.engines:
                move = self.engines[selected_engine].get_move(board, time_limit)
                
                # Kararı kaydet
                decision = {
                    'position_type': position_info['type'].value,
                    'selected_engine': selected_engine,
                    'move': move.uci() if move else None,
                    'position_features': position_info['features'],
                    'confidence': position_info['confidence']
                }
                self.decision_history.append(decision)
                
                logger.info(f"Motor seçildi: {selected_engine} ({position_info['type'].value})")
                return move
            else:
                logger.error(f"Seçilen motor bulunamadı: {selected_engine}")
                return None
                
        except Exception as e:
            logger.error(f"Hibrit motor hatası: {e}")
            return None
    
    def analyze_position_with_all_engines(self, board: chess.Board, 
                                        depth: int = 20) -> Dict[str, Any]:
        """Tüm motorlarla pozisyonu analiz et"""
        results = {}
        
        for engine_name, engine in self.engines.items():
            try:
                analysis = engine.analyze_position(board, depth)
                results[engine_name] = analysis
            except Exception as e:
                logger.error(f"Analiz hatası {engine_name}: {e}")
                results[engine_name] = {}
        
        return results
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Karar istatistiklerini döndür"""
        if not self.decision_history:
            return {}
        
        stats = {
            'total_decisions': len(self.decision_history),
            'engine_usage': {},
            'position_type_usage': {},
            'average_confidence': 0.0
        }
        
        # Motor kullanım istatistikleri
        for decision in self.decision_history:
            engine = decision['selected_engine']
            pos_type = decision['position_type']
            
            stats['engine_usage'][engine] = stats['engine_usage'].get(engine, 0) + 1
            stats['position_type_usage'][pos_type] = stats['position_type_usage'].get(pos_type, 0) + 1
        
        # Ortalama güven skoru
        confidences = [d['confidence'] for d in self.decision_history if d['confidence']]
        if confidences:
            stats['average_confidence'] = sum(confidences) / len(confidences)
        
        return stats
    
    def save_decision_history(self, file_path: Path = None):
        """Karar geçmişini kaydet"""
        if file_path is None:
            file_path = Path("decision_history.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.decision_history, f, indent=2)
            logger.info(f"Karar geçmişi kaydedildi: {file_path}")
        except Exception as e:
            logger.error(f"Karar geçmişi kaydetme hatası: {e}")
    
    def close(self):
        """Tüm motorları kapat"""
        for engine in self.engines.values():
            engine.close()
        logger.info("Hibrit motor sistemi kapatıldı")


class PositionAnalyzer:
    """Pozisyon analiz sistemi"""
    
    def __init__(self):
        self.feature_weights = {
            'piece_count': 0.15,
            'pawn_structure': 0.20,
            'king_safety': 0.15,
            'center_control': 0.15,
            'development': 0.15,
            'tactical_opportunities': 0.20
        }
    
    def analyze_position(self, board: chess.Board) -> Dict[str, Any]:
        """Pozisyonu kapsamlı analiz et"""
        features = {
            'piece_count': self._analyze_piece_count(board),
            'pawn_structure': self._analyze_pawn_structure(board),
            'king_safety': self._analyze_king_safety(board),
            'center_control': self._analyze_center_control(board),
            'development': self._analyze_development(board),
            'tactical_opportunities': self._analyze_tactical_opportunities(board)
        }
        
        # Pozisyon tipini belirle
        position_type = self._classify_position(board, features)
        
        # Güven skorunu hesapla
        confidence = self._calculate_confidence(features)
        
        return {
            'type': position_type,
            'features': features,
            'confidence': confidence,
            'move_number': len(board.move_stack)
        }
    
    def _analyze_piece_count(self, board: chess.Board) -> float:
        """Taş sayısı analizi"""
        piece_map = board.piece_map()
        total_pieces = len(piece_map)
        
        # 32 taş = başlangıç, 6 taş = endgame
        if total_pieces <= 6:
            return 1.0  # Endgame
        elif total_pieces <= 12:
            return 0.7  # Geç orta oyun
        elif total_pieces <= 20:
            return 0.4  # Orta oyun
        else:
            return 0.1  # Açılış
    
    def _analyze_pawn_structure(self, board: chess.Board) -> float:
        """Piyon yapısı analizi"""
        pawns = board.pieces(chess.PAWN, chess.WHITE) | board.pieces(chess.PAWN, chess.BLACK)
        
        if not pawns:
            return 0.0
        
        # Piyon sayısı ve dağılımı
        pawn_count = len(pawns)
        center_pawns = len(pawns & chess.BB_CENTER)
        
        # Piyon yapısı karmaşıklığı
        complexity = center_pawns / pawn_count if pawn_count > 0 else 0
        
        return complexity
    
    def _analyze_king_safety(self, board: chess.Board) -> float:
        """Şah güvenliği analizi"""
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is None or black_king is None:
            return 0.0
        
        # Şahların merkeze yakınlığı
        white_king_rank = chess.square_rank(white_king)
        black_king_rank = chess.square_rank(black_king)
        
        # Şah güvenliği (merkezde = daha az güvenli)
        white_safety = 1.0 - (white_king_rank / 7.0)
        black_safety = 1.0 - (black_king_rank / 7.0)
        
        return (white_safety + black_safety) / 2.0
    
    def _analyze_center_control(self, board: chess.Board) -> float:
        """Merkez kontrolü analizi"""
        center_squares = chess.BB_CENTER
        
        white_control = 0
        black_control = 0
        
        # Merkezdeki taşları say
        for square in chess.scan_forward(center_squares):
            if board.piece_at(square):
                if board.color_at(square) == chess.WHITE:
                    white_control += 1
                else:
                    black_control += 1
        
        total_control = white_control + black_control
        return total_control / 4.0  # 4 merkez karesi
    
    def _analyze_development(self, board: chess.Board) -> float:
        """Gelişim analizi"""
        move_count = len(board.move_stack)
        
        # İlk 10 hamle = açılış
        if move_count <= 10:
            return 0.1
        elif move_count <= 20:
            return 0.3
        elif move_count <= 30:
            return 0.6
        else:
            return 0.9
    
    def _analyze_tactical_opportunities(self, board: chess.Board) -> float:
        """Taktik fırsatları analizi"""
        # Şah tehdidi kontrolü
        if board.is_check():
            return 1.0
        
        # Fork, pin, skewer fırsatları
        tactical_score = 0.0
        
        # Basit taktik analizi
        for move in board.legal_moves:
            board.push(move)
            
            # Şah tehdidi
            if board.is_check():
                tactical_score += 0.3
            
            # Materyal kazanımı
            if board.is_capture(move):
                tactical_score += 0.2
            
            board.pop()
        
        return min(1.0, tactical_score)
    
    def _classify_position(self, board: chess.Board, features: Dict[str, float]) -> PositionType:
        """Pozisyon tipini sınıflandır"""
        move_count = len(board.move_stack)
        
        # Açılış
        if move_count <= 10:
            return PositionType.OPENING
        
        # Endgame
        if features['piece_count'] >= 0.8:
            return PositionType.ENDGAME
        
        # Kapalı pozisyon kontrolü (Stockfish'in zorlandığı)
        if self._is_closed_position(board, features):
            return PositionType.STRATEGIC
        
        # Taktik pozisyon
        if features['tactical_opportunities'] >= 0.5:
            return PositionType.TACTICAL
        
        # Stratejik pozisyon
        if (features['pawn_structure'] >= 0.6 and 
            features['center_control'] >= 0.5):
            return PositionType.STRATEGIC
        
        # Karmaşık pozisyon
        if features['tactical_opportunities'] >= 0.3:
            return PositionType.COMPLEX
        
        return PositionType.SIMPLE
    
    def _is_closed_position(self, board: chess.Board, features: Dict[str, float]) -> bool:
        """Kapalı pozisyon kontrolü"""
        # Piyon yapısı karmaşıklığı
        pawn_complexity = features['pawn_structure']
        
        # Merkez kontrolü düşükse (kapalı merkez)
        center_control = features['center_control']
        
        # Gelişim düşükse (oyun henüz açılmamış)
        development = features['development']
        
        # Kapalı pozisyon kriterleri
        if (pawn_complexity >= 0.7 and  # Karmaşık piyon yapısı
            center_control <= 0.3 and   # Kapalı merkez
            development <= 0.4):        # Henüz açılmamış
            return True
        
        return False
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Analiz güven skorunu hesapla"""
        confidence = 0.0
        
        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 0.1)
            confidence += value * weight
        
        return min(1.0, confidence)


class EngineSelector:
    """Motor seçim sistemi"""
    
    def __init__(self):
        self.engine_preferences = {
            PositionType.OPENING: ["stockfish", "lc0"],
            PositionType.TACTICAL: ["stockfish"],
            PositionType.STRATEGIC: ["lc0", "stockfish"],
            PositionType.ENDGAME: ["stockfish"],
            PositionType.COMPLEX: ["lc0", "stockfish"],
            PositionType.SIMPLE: ["stockfish"]
        }
        
        self.performance_history = {}
        self.adaptation_rate = 0.1
    
    def select_engine(self, position_info: Dict[str, Any], 
                     available_engines: List[str]) -> str:
        """En uygun motoru seç"""
        position_type = position_info['type']
        confidence = position_info['confidence']
        
        # Tercih edilen motorları al
        preferred_engines = self.engine_preferences.get(position_type, ["stockfish"])
        
        # Mevcut motorları filtrele
        available_preferred = [e for e in preferred_engines if e in available_engines]
        
        if not available_preferred:
            # Tercih edilen yoksa mevcut ilk motoru kullan
            return available_engines[0] if available_engines else "stockfish"
        
        # Performans geçmişine göre seçim yap
        if len(available_preferred) > 1:
            return self._select_based_on_performance(available_preferred, position_type)
        else:
            return available_preferred[0]
    
    def _select_based_on_performance(self, engines: List[str], 
                                   position_type: PositionType) -> str:
        """Performans geçmişine göre motor seç"""
        best_engine = engines[0]
        best_score = 0.0
        
        for engine in engines:
            key = f"{engine}_{position_type.value}"
            score = self.performance_history.get(key, 0.5)  # Varsayılan 0.5
            
            if score > best_score:
                best_score = score
                best_engine = engine
        
        return best_engine
    
    def update_performance(self, engine: str, position_type: PositionType, 
                          success: bool):
        """Motor performansını güncelle"""
        key = f"{engine}_{position_type.value}"
        current_score = self.performance_history.get(key, 0.5)
        
        # Başarı durumuna göre skoru güncelle
        if success:
            new_score = current_score + self.adaptation_rate * (1.0 - current_score)
        else:
            new_score = current_score - self.adaptation_rate * current_score
        
        self.performance_history[key] = max(0.0, min(1.0, new_score))
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Performans istatistiklerini döndür"""
        return self.performance_history.copy()


class AdaptiveHybridEngine:
    """Adaptif hibrit motor sistemi"""
    
    def __init__(self):
        self.controller = HybridEngineController()
        self.learning_rate = 0.05
        self.exploration_rate = 0.1
        
    def get_move(self, board: chess.Board, time_limit: float = None) -> Optional[chess.Move]:
        """Adaptif hamle seçimi"""
        # Bazen farklı motorları dene (exploration)
        if np.random.random() < self.exploration_rate:
            return self._explore_alternative_engines(board, time_limit)
        
        # Normal hibrit seçim
        return self.controller.get_best_move(board, time_limit)
    
    def _explore_alternative_engines(self, board: chess.Board, 
                                   time_limit: float = None) -> Optional[chess.Move]:
        """Alternatif motorları dene"""
        available_engines = list(self.controller.engines.keys())
        
        if len(available_engines) < 2:
            return self.controller.get_best_move(board, time_limit)
        
        # Rastgele bir motor seç
        random_engine = np.random.choice(available_engines)
        
        try:
            move = self.controller.engines[random_engine].get_move(board, time_limit)
            logger.info(f"Exploration: {random_engine} motoru denendi")
            return move
        except Exception as e:
            logger.error(f"Exploration hatası: {e}")
            return self.controller.get_best_move(board, time_limit)
    
    def learn_from_result(self, position_info: Dict[str, Any], 
                         selected_engine: str, success: bool):
        """Sonuçtan öğren"""
        position_type = position_info['type']
        self.controller.engine_selector.update_performance(
            selected_engine, position_type, success
        )
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Öğrenme istatistiklerini döndür"""
        return {
            'performance_history': self.controller.engine_selector.get_performance_stats(),
            'decision_history': self.controller.get_decision_statistics(),
            'exploration_rate': self.exploration_rate,
            'learning_rate': self.learning_rate
        }
    
    def close(self):
        """Sistemi kapat"""
        self.controller.close()


def main():
    """Test fonksiyonu"""
    logging.basicConfig(level=logging.INFO)
    
    # Hibrit motor sistemi oluştur
    hybrid_engine = AdaptiveHybridEngine()
    
    try:
        # Test pozisyonu
        board = chess.Board()
        
        # İlk hamle
        move = hybrid_engine.get_move(board)
        if move:
            print(f"İlk hamle: {board.san(move)}")
            board.push(move)
        
        # Pozisyon analizi
        analyzer = PositionAnalyzer()
        position_info = analyzer.analyze_position(board)
        print(f"Pozisyon tipi: {position_info['type'].value}")
        print(f"Güven skoru: {position_info['confidence']:.2f}")
        
        # İstatistikler
        stats = hybrid_engine.get_learning_stats()
        print(f"Performans geçmişi: {stats['performance_history']}")
        
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        hybrid_engine.close()


if __name__ == "__main__":
    main()
