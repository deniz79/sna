"""
Hibrit Motor Test Sistemi
"""

import chess
import chess.pgn
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import numpy as np

from hybrid_engine import AdaptiveHybridEngine, PositionAnalyzer
from engine_wrapper import EngineWrapper

logger = logging.getLogger(__name__)

class HybridEngineTester:
    """Hibrit motor test sistemi"""
    
    def __init__(self):
        self.hybrid_engine = None
        self.stockfish_engine = None
        self.test_positions = []
        self.results = []
        
    def setup_engines(self):
        """Motorları başlat"""
        try:
            self.hybrid_engine = AdaptiveHybridEngine()
            self.stockfish_engine = EngineWrapper("stockfish")
            logger.info("Motorlar başlatıldı")
        except Exception as e:
            logger.error(f"Motor başlatma hatası: {e}")
            raise
    
    def load_test_positions(self, pgn_file: Path = None):
        """Test pozisyonlarını yükle"""
        if pgn_file is None:
            # Varsayılan test pozisyonları
            self.test_positions = self._create_default_positions()
        else:
            self.test_positions = self._load_positions_from_pgn(pgn_file)
        
        logger.info(f"{len(self.test_positions)} test pozisyonu yüklendi")
    
    def _create_default_positions(self) -> List[Dict[str, Any]]:
        """Varsayılan test pozisyonları oluştur"""
        positions = []
        
        # Açılış pozisyonları
        positions.append({
            'name': 'Starting Position',
            'fen': chess.Board().fen(),
            'expected_type': 'opening'
        })
        
        # Sicilian Defense
        board = chess.Board()
        moves = ['e4', 'c5', 'Nf3', 'd6', 'd4', 'cxd4', 'Nxd4', 'Nf6', 'Nc3', 'a6']
        for move in moves:
            board.push_san(move)
        positions.append({
            'name': 'Sicilian Defense',
            'fen': board.fen(),
            'expected_type': 'strategic'
        })
        
        # Tactical position
        board = chess.Board()
        moves = ['e4', 'e5', 'Nf3', 'Nc6', 'Bc4', 'Bc5', 'b4', 'Bxb4', 'c3', 'Ba5', 'd4', 'exd4', 'O-O']
        for move in moves:
            board.push_san(move)
        positions.append({
            'name': 'Evans Gambit',
            'fen': board.fen(),
            'expected_type': 'tactical'
        })
        
        # Endgame position
        board = chess.Board('8/8/8/8/8/8/4K3/4k3 w - - 0 1')
        positions.append({
            'name': 'King vs King',
            'fen': board.fen(),
            'expected_type': 'endgame'
        })
        
        return positions
    
    def _load_positions_from_pgn(self, pgn_file: Path) -> List[Dict[str, Any]]:
        """PGN dosyasından pozisyonları yükle"""
        positions = []
        
        try:
            with open(pgn_file, 'r') as f:
                game_count = 0
                while game_count < 50:  # Maksimum 50 oyun
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    board = game.board()
                    moves = list(game.mainline_moves())
                    
                    # Farklı aşamalardan pozisyonlar al
                    checkpoints = [5, 10, 15, 20, 25]
                    for checkpoint in checkpoints:
                        if checkpoint < len(moves):
                            temp_board = board.copy()
                            for i in range(checkpoint):
                                temp_board.push(moves[i])
                            
                            positions.append({
                                'name': f'Game {game_count} Move {checkpoint}',
                                'fen': temp_board.fen(),
                                'expected_type': 'unknown'
                            })
                    
                    game_count += 1
                    
        except Exception as e:
            logger.error(f"PGN yükleme hatası: {e}")
        
        return positions
    
    def test_position_analysis(self) -> Dict[str, Any]:
        """Pozisyon analizi testi"""
        logger.info("Pozisyon analizi testi başlatılıyor...")
        
        analyzer = PositionAnalyzer()
        results = {
            'total_positions': len(self.test_positions),
            'analysis_results': [],
            'type_accuracy': 0.0
        }
        
        correct_classifications = 0
        
        for i, position in enumerate(self.test_positions):
            try:
                board = chess.Board(position['fen'])
                position_info = analyzer.analyze_position(board)
                
                result = {
                    'position_name': position['name'],
                    'detected_type': position_info['type'].value,
                    'expected_type': position['expected_type'],
                    'confidence': position_info['confidence'],
                    'features': position_info['features']
                }
                
                results['analysis_results'].append(result)
                
                # Doğru sınıflandırma kontrolü
                if position['expected_type'] != 'unknown':
                    if position_info['type'].value == position['expected_type']:
                        correct_classifications += 1
                
                logger.info(f"Pozisyon {i+1}: {position['name']} -> {position_info['type'].value}")
                
            except Exception as e:
                logger.error(f"Pozisyon analiz hatası {i}: {e}")
        
        # Doğruluk oranını hesapla
        if results['total_positions'] > 0:
            results['type_accuracy'] = correct_classifications / results['total_positions']
        
        logger.info(f"Pozisyon analizi tamamlandı. Doğruluk: {results['type_accuracy']:.2%}")
        return results
    
    def test_engine_selection(self) -> Dict[str, Any]:
        """Motor seçim testi"""
        logger.info("Motor seçim testi başlatılıyor...")
        
        results = {
            'total_positions': len(self.test_positions),
            'selection_results': [],
            'engine_usage': {},
            'average_confidence': 0.0
        }
        
        total_confidence = 0.0
        
        for i, position in enumerate(self.test_positions):
            try:
                board = chess.Board(position['fen'])
                
                # Hibrit motorla hamle al
                start_time = time.time()
                move = self.hybrid_engine.get_move(board)
                end_time = time.time()
                
                # Karar istatistiklerini al
                decision_stats = self.hybrid_engine.get_learning_stats()
                
                result = {
                    'position_name': position['name'],
                    'selected_move': move.uci() if move else None,
                    'decision_time': end_time - start_time,
                    'engine_usage': decision_stats['decision_history'].get('engine_usage', {}),
                    'position_type_usage': decision_stats['decision_history'].get('position_type_usage', {})
                }
                
                results['selection_results'].append(result)
                
                # Motor kullanım istatistiklerini güncelle
                for engine, count in result['engine_usage'].items():
                    results['engine_usage'][engine] = results['engine_usage'].get(engine, 0) + count
                
                logger.info(f"Pozisyon {i+1}: {position['name']} -> {move.uci() if move else 'None'}")
                
            except Exception as e:
                logger.error(f"Motor seçim hatası {i}: {e}")
        
        # Ortalama güven skorunu hesapla
        if results['total_positions'] > 0:
            results['average_confidence'] = total_confidence / results['total_positions']
        
        logger.info("Motor seçim testi tamamlandı")
        return results
    
    def compare_engines(self) -> Dict[str, Any]:
        """Motorları karşılaştır"""
        logger.info("Motor karşılaştırma testi başlatılıyor...")
        
        results = {
            'total_positions': len(self.test_positions),
            'comparison_results': [],
            'hybrid_wins': 0,
            'stockfish_wins': 0,
            'draws': 0
        }
        
        for i, position in enumerate(self.test_positions):
            try:
                board = chess.Board(position['fen'])
                
                # Hibrit motor analizi
                hybrid_start = time.time()
                hybrid_move = self.hybrid_engine.get_move(board)
                hybrid_time = time.time() - hybrid_start
                
                # Stockfish analizi
                stockfish_start = time.time()
                stockfish_move = self.stockfish_engine.get_move(board)
                stockfish_time = time.time() - stockfish_start
                
                # Hamle kalitesini karşılaştır (basit ölçüm)
                hybrid_quality = self._evaluate_move_quality(board, hybrid_move)
                stockfish_quality = self._evaluate_move_quality(board, stockfish_move)
                
                result = {
                    'position_name': position['name'],
                    'hybrid_move': hybrid_move.uci() if hybrid_move else None,
                    'stockfish_move': stockfish_move.uci() if stockfish_move else None,
                    'hybrid_time': hybrid_time,
                    'stockfish_time': stockfish_time,
                    'hybrid_quality': hybrid_quality,
                    'stockfish_quality': stockfish_quality,
                    'winner': 'hybrid' if hybrid_quality > stockfish_quality else 'stockfish' if stockfish_quality > hybrid_quality else 'draw'
                }
                
                results['comparison_results'].append(result)
                
                # Kazanan sayısını güncelle
                if result['winner'] == 'hybrid':
                    results['hybrid_wins'] += 1
                elif result['winner'] == 'stockfish':
                    results['stockfish_wins'] += 1
                else:
                    results['draws'] += 1
                
                logger.info(f"Pozisyon {i+1}: {result['winner']} kazandı")
                
            except Exception as e:
                logger.error(f"Motor karşılaştırma hatası {i}: {e}")
        
        logger.info("Motor karşılaştırma testi tamamlandı")
        return results
    
    def _evaluate_move_quality(self, board: chess.Board, move: chess.Move) -> float:
        """Hamle kalitesini değerlendir (basit ölçüm)"""
        if not move:
            return 0.0
        
        quality = 0.0
        
        # Materyal kazanımı
        if board.is_capture(move):
            quality += 1.0
        
        # Şah tehdidi
        board.push(move)
        if board.is_check():
            quality += 0.5
        board.pop()
        
        # Merkez kontrolü
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        if move.to_square in center_squares:
            quality += 0.3
        
        return quality
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Kapsamlı test çalıştır"""
        logger.info("Kapsamlı hibrit motor testi başlatılıyor...")
        
        # Motorları başlat
        self.setup_engines()
        
        # Test pozisyonlarını yükle
        self.load_test_positions()
        
        # Testleri çalıştır
        position_analysis = self.test_position_analysis()
        engine_selection = self.test_engine_selection()
        engine_comparison = self.compare_engines()
        
        # Sonuçları birleştir
        comprehensive_results = {
            'position_analysis': position_analysis,
            'engine_selection': engine_selection,
            'engine_comparison': engine_comparison,
            'summary': {
                'total_tests': len(self.test_positions),
                'position_accuracy': position_analysis['type_accuracy'],
                'hybrid_performance': engine_comparison['hybrid_wins'] / max(1, engine_comparison['total_positions']),
                'stockfish_performance': engine_comparison['stockfish_wins'] / max(1, engine_comparison['total_positions'])
            }
        }
        
        # Sonuçları kaydet
        self._save_results(comprehensive_results)
        
        # Grafikleri oluştur
        self._create_visualizations(comprehensive_results)
        
        logger.info("Kapsamlı test tamamlandı")
        return comprehensive_results
    
    def _save_results(self, results: Dict[str, Any]):
        """Sonuçları kaydet"""
        timestamp = int(time.time())
        results_file = Path(f"hybrid_test_results_{timestamp}.json")
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Sonuçlar kaydedildi: {results_file}")
        except Exception as e:
            logger.error(f"Sonuç kaydetme hatası: {e}")
    
    def _create_visualizations(self, results: Dict[str, Any]):
        """Görselleştirmeler oluştur"""
        try:
            # Motor kullanım grafiği
            engine_usage = results['engine_selection']['engine_usage']
            if engine_usage:
                plt.figure(figsize=(10, 6))
                engines = list(engine_usage.keys())
                counts = list(engine_usage.values())
                
                plt.bar(engines, counts, color=['#ff9999', '#66b3ff', '#99ff99'])
                plt.title('Motor Kullanım Dağılımı')
                plt.ylabel('Kullanım Sayısı')
                plt.xlabel('Motor')
                
                plt.savefig('engine_usage.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Performans karşılaştırması
            comparison = results['engine_comparison']
            if comparison['total_positions'] > 0:
                plt.figure(figsize=(8, 6))
                labels = ['Hibrit', 'Stockfish', 'Beraberlik']
                sizes = [comparison['hybrid_wins'], comparison['stockfish_wins'], comparison['draws']]
                colors = ['#ff9999', '#66b3ff', '#99ff99']
                
                plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                plt.title('Motor Performans Karşılaştırması')
                
                plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            logger.info("Görselleştirmeler oluşturuldu")
            
        except Exception as e:
            logger.error(f"Görselleştirme hatası: {e}")
    
    def close(self):
        """Test sistemini kapat"""
        if self.hybrid_engine:
            self.hybrid_engine.close()
        if self.stockfish_engine:
            self.stockfish_engine.close()
        logger.info("Test sistemi kapatıldı")


def main():
    """Ana test fonksiyonu"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tester = HybridEngineTester()
    
    try:
        results = tester.run_comprehensive_test()
        
        # Özet sonuçları yazdır
        summary = results['summary']
        print("\n" + "="*50)
        print("HİBRİT MOTOR TEST SONUÇLARI")
        print("="*50)
        print(f"Toplam Test: {summary['total_tests']}")
        print(f"Pozisyon Analiz Doğruluğu: {summary['position_accuracy']:.2%}")
        print(f"Hibrit Motor Performansı: {summary['hybrid_performance']:.2%}")
        print(f"Stockfish Performansı: {summary['stockfish_performance']:.2%}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Test hatası: {e}")
    finally:
        tester.close()


if __name__ == "__main__":
    main()
