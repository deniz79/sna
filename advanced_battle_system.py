#!/usr/bin/env python3
"""
Gelişmiş Savaş Sistemi
Pozisyon analizi, öğrenme ve otomatik optimizasyon
"""

import chess
import chess.engine
import chess.pgn
import time
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
from advanced_hybrid_engine import AdvancedHybridEngine, PositionType, EngineType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedBattleSystem:
    """Gelişmiş savaş sistemi"""
    
    def __init__(self):
        self.hybrid_engine = AdvancedHybridEngine()
        self.stockfish = None
        self.battle_history = []
        self.weak_positions = []
        self.performance_metrics = {}
        
        # Stockfish'i başlat
        self._initialize_stockfish()
    
    def _initialize_stockfish(self):
        """Stockfish'i başlat"""
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
    
    def run_advanced_battle(self, num_games: int = 10, time_control: str = "5+3") -> Dict:
        """Gelişmiş savaş sistemi"""
        print("🚀 Gelişmiş Savaş Sistemi Başlıyor!")
        print("=" * 60)
        
        results = {
            'wins': 0, 'losses': 0, 'draws': 0,
            'position_analysis': {},
            'engine_performance': {},
            'weak_positions': [],
            'learning_insights': []
        }
        
        for game_num in range(1, num_games + 1):
            print(f"\n🎮 OYUN {game_num}/{num_games}")
            print("-" * 40)
            
            game_result = self._play_single_game(time_control)
            
            # Sonuçları kaydet
            if game_result['result'] == "1-0":
                results['wins'] += 1
                print("🎉 KAZANDIK!")
            elif game_result['result'] == "0-1":
                results['losses'] += 1
                print("😔 Kaybettik")
            else:
                results['draws'] += 1
                print("🤝 Beraberlik")
            
            # Pozisyon analizini kaydet
            self._analyze_game_positions(game_result)
            
            # Zayıf pozisyonları tespit et
            weak_positions = self._identify_weak_positions(game_result)
            results['weak_positions'].extend(weak_positions)
            
            # Öğrenme içgörüleri
            insights = self._extract_learning_insights(game_result)
            results['learning_insights'].extend(insights)
            
            # Kısa bekleme
            time.sleep(1)
        
        # Final analiz
        self._generate_final_analysis(results)
        
        return results
    
    def _play_single_game(self, time_control: str) -> Dict:
        """Tek oyun oyna"""
        board = chess.Board()
        moves = []
        position_analyses = []
        engine_decisions = []
        
        move_count = 0
        moves_without_capture = 0
        
        while not board.is_game_over() and move_count < 200:
            move_count += 1
            
            if board.turn == chess.WHITE:
                # Bizim hibrit motor
                print(f"{move_count}. Beyaz (Hibrit) düşünüyor...")
                
                # Pozisyon analizi
                analysis = self.hybrid_engine.analyzer.analyze_position(board)
                position_analyses.append({
                    'move': move_count,
                    'position_type': analysis.position_type.value,
                    'confidence': analysis.confidence,
                    'features': analysis.features,
                    'recommended_engine': analysis.recommended_engine.value,
                    'time_allocation': analysis.time_allocation,
                    'depth_allocation': analysis.depth_allocation
                })
                
                start_time = time.time()
                move = self.hybrid_engine.get_move(board, analysis.time_allocation)
                end_time = time.time()
                
                if move:
                    san_move = board.san(move)
                    think_time = end_time - start_time
                    
                    engine_decisions.append({
                        'move': move_count,
                        'engine_used': analysis.recommended_engine.value,
                        'move_san': san_move,
                        'move_uci': move.uci(),
                        'think_time': think_time,
                        'position_type': analysis.position_type.value
                    })
                    
                    print(f"   {san_move} ({move.uci()}) - {analysis.position_type.value} - {analysis.recommended_engine.value} - {think_time:.2f}s")
                    
                    # 50 hamle kuralı
                    if board.is_capture(move):
                        moves_without_capture = 0
                    else:
                        moves_without_capture += 1
                    
                    board.push(move)
                    
                    if moves_without_capture >= 100:
                        print("   50 hamle kuralı! Beraberlik")
                        break
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
                    
            else:
                # Stockfish
                print(f"{move_count}. Siyah (Stockfish) düşünüyor...")
                
                start_time = time.time()
                result = self.stockfish.play(board, chess.engine.Limit(time=2.0))
                end_time = time.time()
                
                if result.move:
                    san_move = board.san(result.move)
                    think_time = end_time - start_time
                    
                    print(f"   {san_move} ({result.move.uci()}) - Stockfish - {think_time:.2f}s")
                    
                    # 50 hamle kuralı
                    if board.is_capture(result.move):
                        moves_without_capture = 0
                    else:
                        moves_without_capture += 1
                    
                    board.push(result.move)
                    
                    if moves_without_capture >= 100:
                        print("   50 hamle kuralı! Beraberlik")
                        break
                else:
                    print("   ❌ Hamle bulunamadı!")
                    break
            
            moves.append({
                'move': move_count,
                'fen': board.fen(),
                'turn': 'white' if board.turn == chess.WHITE else 'black'
            })
        
        return {
            'result': board.result(),
            'moves': moves,
            'position_analyses': position_analyses,
            'engine_decisions': engine_decisions,
            'final_fen': board.fen(),
            'move_count': move_count
        }
    
    def _analyze_game_positions(self, game_result: Dict):
        """Oyun pozisyonlarını analiz et"""
        position_types = {}
        
        for analysis in game_result['position_analyses']:
            pos_type = analysis['position_type']
            position_types[pos_type] = position_types.get(pos_type, 0) + 1
        
        # Pozisyon tipi dağılımını kaydet
        for pos_type, count in position_types.items():
            if pos_type not in self.performance_metrics:
                self.performance_metrics[pos_type] = {'count': 0, 'wins': 0, 'losses': 0, 'draws': 0}
            
            self.performance_metrics[pos_type]['count'] += count
            
            # Sonuca göre skor
            if game_result['result'] == "1-0":
                self.performance_metrics[pos_type]['wins'] += count
            elif game_result['result'] == "0-1":
                self.performance_metrics[pos_type]['losses'] += count
            else:
                self.performance_metrics[pos_type]['draws'] += count
    
    def _identify_weak_positions(self, game_result: Dict) -> List[Dict]:
        """Zayıf pozisyonları tespit et"""
        weak_positions = []
        
        if game_result['result'] != "1-0":  # Sadece kayıp/beraberlik oyunlarında
            for i, analysis in enumerate(game_result['position_analyses']):
                # Düşük güven skorlu pozisyonlar
                if analysis['confidence'] < 0.5:
                    weak_positions.append({
                        'move': analysis['move'],
                        'fen': game_result['moves'][i]['fen'],
                        'position_type': analysis['position_type'],
                        'confidence': analysis['confidence'],
                        'features': analysis['features'],
                        'reason': 'low_confidence'
                    })
                
                # Kritik pozisyonlarda yanlış motor seçimi
                if (analysis['position_type'] == 'critical' and 
                    analysis['recommended_engine'] != 'stockfish'):
                    weak_positions.append({
                        'move': analysis['move'],
                        'fen': game_result['moves'][i]['fen'],
                        'position_type': analysis['position_type'],
                        'confidence': analysis['confidence'],
                        'features': analysis['features'],
                        'reason': 'wrong_engine_selection'
                    })
        
        return weak_positions
    
    def _extract_learning_insights(self, game_result: Dict) -> List[Dict]:
        """Öğrenme içgörüleri çıkar"""
        insights = []
        
        # Motor performans analizi
        engine_performance = {}
        for decision in game_result['engine_decisions']:
            engine = decision['engine_used']
            if engine not in engine_performance:
                engine_performance[engine] = {'moves': 0, 'avg_time': 0.0}
            
            engine_performance[engine]['moves'] += 1
            engine_performance[engine]['avg_time'] += decision['think_time']
        
        # Ortalama süreleri hesapla
        for engine, stats in engine_performance.items():
            if stats['moves'] > 0:
                stats['avg_time'] /= stats['moves']
        
        insights.append({
            'type': 'engine_performance',
            'data': engine_performance,
            'game_result': game_result['result']
        })
        
        # Pozisyon tipi performansı
        position_performance = {}
        for analysis in game_result['position_analyses']:
            pos_type = analysis['position_type']
            if pos_type not in position_performance:
                position_performance[pos_type] = {'count': 0, 'avg_confidence': 0.0}
            
            position_performance[pos_type]['count'] += 1
            position_performance[pos_type]['avg_confidence'] += analysis['confidence']
        
        # Ortalama güven skorlarını hesapla
        for pos_type, stats in position_performance.items():
            if stats['count'] > 0:
                stats['avg_confidence'] /= stats['count']
        
        insights.append({
            'type': 'position_performance',
            'data': position_performance,
            'game_result': game_result['result']
        })
        
        return insights
    
    def _generate_final_analysis(self, results: Dict):
        """Final analiz raporu oluştur"""
        print("\n" + "=" * 60)
        print("📊 FİNAL ANALİZ RAPORU")
        print("=" * 60)
        
        total_games = sum([results['wins'], results['losses'], results['draws']])
        win_rate = (results['wins'] / total_games * 100) if total_games > 0 else 0
        
        print(f"🎯 Genel Performans:")
        print(f"   Kazanma: {results['wins']} ({win_rate:.1f}%)")
        print(f"   Kayıp: {results['losses']}")
        print(f"   Beraberlik: {results['draws']}")
        
        # Pozisyon tipi performansı
        print(f"\n📈 Pozisyon Tipi Performansı:")
        for pos_type, metrics in self.performance_metrics.items():
            total = metrics['count']
            if total > 0:
                win_rate = (metrics['wins'] / total * 100)
                print(f"   {pos_type}: {win_rate:.1f}% kazanma ({total} pozisyon)")
        
        # Motor performansı
        print(f"\n🔧 Motor Performansı:")
        hybrid_stats = self.hybrid_engine.get_performance_stats()
        for engine, stats in hybrid_stats['engine_performance'].items():
            print(f"   {engine}: Ortalama derinlik {stats['avg_depth']:.1f}, süre {stats['avg_time']:.2f}s")
        
        # Zayıf pozisyonlar
        print(f"\n⚠️  Zayıf Pozisyonlar ({len(results['weak_positions'])} tespit edildi):")
        weak_reasons = {}
        for pos in results['weak_positions']:
            reason = pos['reason']
            weak_reasons[reason] = weak_reasons.get(reason, 0) + 1
        
        for reason, count in weak_reasons.items():
            print(f"   {reason}: {count} pozisyon")
        
        # Öğrenme önerileri
        print(f"\n💡 Öğrenme Önerileri:")
        self._generate_learning_recommendations(results)
        
        # Raporu kaydet
        self._save_analysis_report(results)
        
        # Görselleştirme oluştur
        self._create_visualizations(results)
    
    def _generate_learning_recommendations(self, results: Dict):
        """Öğrenme önerileri oluştur"""
        recommendations = []
        
        # Zayıf pozisyon analizi
        if len(results['weak_positions']) > 0:
            low_confidence_count = sum(1 for pos in results['weak_positions'] if pos['reason'] == 'low_confidence')
            wrong_engine_count = sum(1 for pos in results['weak_positions'] if pos['reason'] == 'wrong_engine_selection')
            
            if low_confidence_count > 0:
                recommendations.append(f"Pozisyon analiz algoritmasını iyileştir ({low_confidence_count} düşük güven)")
            
            if wrong_engine_count > 0:
                recommendations.append(f"Motor seçim algoritmasını optimize et ({wrong_engine_count} yanlış seçim)")
        
        # Pozisyon tipi performansı
        for pos_type, metrics in self.performance_metrics.items():
            if metrics['count'] > 5:  # Yeterli veri varsa
                win_rate = (metrics['wins'] / metrics['count'] * 100)
                if win_rate < 40:
                    recommendations.append(f"{pos_type} pozisyonlarında daha iyi strateji geliştir ({win_rate:.1f}% kazanma)")
        
        # Önerileri yazdır
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    def _save_analysis_report(self, results: Dict):
        """Analiz raporunu kaydet"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'performance_metrics': self.performance_metrics,
            'hybrid_stats': self.hybrid_engine.get_performance_stats()
        }
        
        report_file = Path("data/analysis_reports") / f"battle_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Rapor kaydedildi: {report_file}")
    
    def _create_visualizations(self, results: Dict):
        """Görselleştirmeler oluştur"""
        try:
            # Pozisyon tipi dağılımı
            pos_types = list(self.performance_metrics.keys())
            counts = [self.performance_metrics[pos]['count'] for pos in pos_types]
            
            plt.figure(figsize=(12, 8))
            
            # Alt grafik 1: Pozisyon tipi dağılımı
            plt.subplot(2, 2, 1)
            plt.pie(counts, labels=pos_types, autopct='%1.1f%%')
            plt.title('Pozisyon Tipi Dağılımı')
            
            # Alt grafik 2: Kazanma oranları
            plt.subplot(2, 2, 2)
            win_rates = []
            for pos in pos_types:
                metrics = self.performance_metrics[pos]
                if metrics['count'] > 0:
                    win_rate = (metrics['wins'] / metrics['count'] * 100)
                    win_rates.append(win_rate)
                else:
                    win_rates.append(0)
            
            plt.bar(pos_types, win_rates)
            plt.title('Pozisyon Tipine Göre Kazanma Oranı')
            plt.ylabel('Kazanma Oranı (%)')
            plt.xticks(rotation=45)
            
            # Alt grafik 3: Motor kullanımı
            plt.subplot(2, 2, 3)
            engine_usage = {}
            for decision in results.get('engine_decisions', []):
                engine = decision['engine_used']
                engine_usage[engine] = engine_usage.get(engine, 0) + 1
            
            if engine_usage:
                engines = list(engine_usage.keys())
                usage_counts = list(engine_usage.values())
                plt.bar(engines, usage_counts)
                plt.title('Motor Kullanım Dağılımı')
                plt.ylabel('Kullanım Sayısı')
            
            # Alt grafik 4: Zaman analizi
            plt.subplot(2, 2, 4)
            think_times = [decision['think_time'] for decision in results.get('engine_decisions', [])]
            if think_times:
                plt.hist(think_times, bins=20, alpha=0.7)
                plt.title('Düşünme Süresi Dağılımı')
                plt.xlabel('Süre (saniye)')
                plt.ylabel('Frekans')
            
            plt.tight_layout()
            
            # Grafiği kaydet
            plot_file = Path("data/analysis_reports") / f"battle_visualization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Görselleştirme kaydedildi: {plot_file}")
            
        except Exception as e:
            logger.error(f"Görselleştirme hatası: {e}")
    
    def close(self):
        """Sistemi kapat"""
        if self.stockfish:
            self.stockfish.quit()
        if self.hybrid_engine:
            self.hybrid_engine.close()

def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gelişmiş Savaş Sistemi")
    parser.add_argument("--games", type=int, default=10, help="Oyun sayısı")
    parser.add_argument("--time", default="5+3", help="Zaman kontrolü")
    
    args = parser.parse_args()
    
    battle_system = AdvancedBattleSystem()
    
    try:
        results = battle_system.run_advanced_battle(args.games, args.time)
        
        print(f"\n🎉 Analiz tamamlandı!")
        print(f"Toplam {args.games} oyun oynandı")
        print(f"Kazanma oranı: {results['wins']/args.games*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⏹️  Analiz durduruldu")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
    finally:
        battle_system.close()

if __name__ == "__main__":
    main()
