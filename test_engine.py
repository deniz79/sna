"""
Test Sistemi - Cutechess-cli ile otomatik test ve analiz
"""

import chess
import chess.pgn
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import config
from engine_wrapper import EngineWrapper

logger = logging.getLogger(__name__)

class TestEngine:
    """Motor test sistemi"""
    
    def __init__(self):
        self.test_config = config.TEST_CONFIG
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def create_engine_config(self, engine_name: str, engine_path: str) -> Dict:
        """Motor konfigürasyonu oluştur"""
        return {
            "name": engine_name,
            "command": engine_path,
            "protocol": "uci",
            "options": config.ENGINES.get(engine_name, {}).get("options", {})
        }
    
    def run_cutechess_test(self, engine1: str, engine2: str, 
                          games: int = None, concurrency: int = None) -> Path:
        """Cutechess-cli ile test çalıştır"""
        if games is None:
            games = self.test_config["games_per_test"]
        if concurrency is None:
            concurrency = self.test_config["concurrency"]
        
        # Motor yollarını al
        engine1_path = config.get_engine_path(engine1)
        engine2_path = config.get_engine_path(engine2)
        
        if not engine1_path or not Path(engine1_path).exists():
            raise FileNotFoundError(f"Motor bulunamadı: {engine1_path}")
        if not engine2_path or not Path(engine2_path).exists():
            raise FileNotFoundError(f"Motor bulunamadı: {engine2_path}")
        
        # Çıktı dosyası
        timestamp = int(time.time())
        output_pgn = self.results_dir / f"test_{engine1}_vs_{engine2}_{timestamp}.pgn"
        
        # Cutechess komutu
        cmd = [
            "cutechess-cli",
            "-engine", f"cmd={engine1_path}", f"name={engine1}",
            "-engine", f"cmd={engine2_path}", f"name={engine2}",
            "-each", f"tc={config.GAME_CONFIG['time_control']}",
            "-games", str(games),
            "-concurrency", str(concurrency),
            "-pgnout", str(output_pgn),
            "-repeat",
            "-recover"
        ]
        
        logger.info(f"Test başlatılıyor: {' '.join(cmd)}")
        
        try:
            # Testi çalıştır
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Test tamamlandı: {output_pgn}")
            logger.info(f"Çıktı: {result.stdout}")
            
            return output_pgn
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Test hatası: {e.stderr}")
            raise
    
    def analyze_test_results(self, pgn_file: Path) -> Dict:
        """Test sonuçlarını analiz et"""
        results = {
            'total_games': 0,
            'engine1_wins': 0,
            'engine2_wins': 0,
            'draws': 0,
            'engine1_win_rate': 0.0,
            'engine2_win_rate': 0.0,
            'draw_rate': 0.0,
            'avg_moves': 0,
            'game_results': [],
            'opening_analysis': {},
            'time_analysis': {}
        }
        
        try:
            with open(pgn_file, 'r') as f:
                game_count = 0
                total_moves = 0
                
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    
                    game_count += 1
                    moves = list(game.mainline_moves())
                    total_moves += len(moves)
                    
                    # Oyun sonucu
                    result = game.headers.get("Result", "")
                    white_player = game.headers.get("White", "")
                    black_player = game.headers.get("Black", "")
                    
                    game_result = {
                        'game_number': game_count,
                        'result': result,
                        'white': white_player,
                        'black': black_player,
                        'moves': len(moves),
                        'opening': game.headers.get("ECO", ""),
                        'time_control': game.headers.get("TimeControl", "")
                    }
                    
                    results['game_results'].append(game_result)
                    
                    # Sonuç sayılarını güncelle
                    if result == "1-0":
                        if white_player == self.test_config["engine1"]:
                            results['engine1_wins'] += 1
                        else:
                            results['engine2_wins'] += 1
                    elif result == "0-1":
                        if black_player == self.test_config["engine1"]:
                            results['engine1_wins'] += 1
                        else:
                            results['engine2_wins'] += 1
                    elif result == "1/2-1/2":
                        results['draws'] += 1
                    
                    # Açılış analizi
                    opening = game.headers.get("ECO", "Unknown")
                    if opening not in results['opening_analysis']:
                        results['opening_analysis'][opening] = {
                            'games': 0,
                            'engine1_wins': 0,
                            'engine2_wins': 0,
                            'draws': 0
                        }
                    
                    results['opening_analysis'][opening]['games'] += 1
                    if result == "1-0":
                        if white_player == self.test_config["engine1"]:
                            results['opening_analysis'][opening]['engine1_wins'] += 1
                        else:
                            results['opening_analysis'][opening]['engine2_wins'] += 1
                    elif result == "0-1":
                        if black_player == self.test_config["engine1"]:
                            results['opening_analysis'][opening]['engine1_wins'] += 1
                        else:
                            results['opening_analysis'][opening]['engine2_wins'] += 1
                    elif result == "1/2-1/2":
                        results['opening_analysis'][opening]['draws'] += 1
            
            # İstatistikleri hesapla
            results['total_games'] = game_count
            if game_count > 0:
                results['engine1_win_rate'] = results['engine1_wins'] / game_count
                results['engine2_win_rate'] = results['engine2_wins'] / game_count
                results['draw_rate'] = results['draws'] / game_count
                results['avg_moves'] = total_moves / game_count
            
            logger.info(f"Analiz tamamlandı: {game_count} oyun")
            
        except Exception as e:
            logger.error(f"Sonuç analiz hatası: {e}")
        
        return results
    
    def generate_test_report(self, results: Dict, output_file: Path = None) -> Path:
        """Test raporu oluştur"""
        if output_file is None:
            timestamp = int(time.time())
            output_file = self.results_dir / f"test_report_{timestamp}.html"
        
        try:
            # HTML raporu oluştur
            html_content = self._create_html_report(results)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Rapor oluşturuldu: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Rapor oluşturma hatası: {e}")
            raise
    
    def _create_html_report(self, results: Dict) -> str:
        """HTML raporu oluştur"""
        engine1 = self.test_config["engine1"]
        engine2 = self.test_config["engine2"]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Raporu: {engine1} vs {engine2}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; }}
                .chart {{ margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Raporu: {engine1} vs {engine2}</h1>
                <p>Toplam Oyun: {results['total_games']}</p>
            </div>
            
            <div class="stats">
                <div class="stat-box">
                    <h3>{engine1} Kazanma Oranı</h3>
                    <p>{results['engine1_win_rate']:.2%}</p>
                    <p>Kazanma: {results['engine1_wins']}</p>
                </div>
                <div class="stat-box">
                    <h3>Beraberlik Oranı</h3>
                    <p>{results['draw_rate']:.2%}</p>
                    <p>Beraberlik: {results['draws']}</p>
                </div>
                <div class="stat-box">
                    <h3>{engine2} Kazanma Oranı</h3>
                    <p>{results['engine2_win_rate']:.2%}</p>
                    <p>Kazanma: {results['engine2_wins']}</p>
                </div>
            </div>
            
            <div class="chart">
                <h2>Genel İstatistikler</h2>
                <p>Ortalama Hamle Sayısı: {results['avg_moves']:.1f}</p>
            </div>
            
            <div class="chart">
                <h2>Açılış Analizi</h2>
                <table>
                    <tr>
                        <th>Açılış</th>
                        <th>Oyun Sayısı</th>
                        <th>{engine1} Kazanma</th>
                        <th>{engine2} Kazanma</th>
                        <th>Beraberlik</th>
                    </tr>
        """
        
        for opening, data in results['opening_analysis'].items():
            html += f"""
                    <tr>
                        <td>{opening}</td>
                        <td>{data['games']}</td>
                        <td>{data['engine1_wins']}</td>
                        <td>{data['engine2_wins']}</td>
                        <td>{data['draws']}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_performance_charts(self, results: Dict, output_dir: Path = None) -> List[Path]:
        """Performans grafikleri oluştur"""
        if output_dir is None:
            output_dir = self.results_dir
        
        chart_files = []
        
        try:
            # Sonuç dağılımı grafiği
            plt.figure(figsize=(10, 6))
            labels = [f"{self.test_config['engine1']} Kazanma", 
                     "Beraberlik", 
                     f"{self.test_config['engine2']} Kazanma"]
            sizes = [results['engine1_wins'], results['draws'], results['engine2_wins']]
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Test Sonuçları Dağılımı')
            
            chart_file = output_dir / "results_pie_chart.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            chart_files.append(chart_file)
            
            # Açılış performansı grafiği
            if results['opening_analysis']:
                plt.figure(figsize=(12, 8))
                
                openings = list(results['opening_analysis'].keys())[:10]  # İlk 10 açılış
                engine1_rates = []
                engine2_rates = []
                
                for opening in openings:
                    data = results['opening_analysis'][opening]
                    total = data['games']
                    if total > 0:
                        engine1_rates.append(data['engine1_wins'] / total)
                        engine2_rates.append(data['engine2_wins'] / total)
                    else:
                        engine1_rates.append(0)
                        engine2_rates.append(0)
                
                x = range(len(openings))
                width = 0.35
                
                plt.bar([i - width/2 for i in x], engine1_rates, width, 
                       label=self.test_config['engine1'], color='#ff9999')
                plt.bar([i + width/2 for i in x], engine2_rates, width, 
                       label=self.test_config['engine2'], color='#99ff99')
                
                plt.xlabel('Açılışlar')
                plt.ylabel('Kazanma Oranı')
                plt.title('Açılış Bazında Performans')
                plt.xticks(x, openings, rotation=45)
                plt.legend()
                plt.tight_layout()
                
                chart_file = output_dir / "opening_performance.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
            
            logger.info(f"{len(chart_files)} grafik oluşturuldu")
            
        except Exception as e:
            logger.error(f"Grafik oluşturma hatası: {e}")
        
        return chart_files
    
    def run_comprehensive_test(self, engine1: str, engine2: str, 
                             games: int = 100) -> Dict:
        """Kapsamlı test çalıştır"""
        logger.info(f"Kapsamlı test başlatılıyor: {engine1} vs {engine2}")
        
        # Test çalıştır
        pgn_file = self.run_cutechess_test(engine1, engine2, games)
        
        # Sonuçları analiz et
        results = self.analyze_test_results(pgn_file)
        
        # Rapor oluştur
        report_file = self.generate_test_report(results)
        
        # Grafikler oluştur
        chart_files = self.create_performance_charts(results)
        
        # JSON sonuçları kaydet
        json_file = self.results_dir / f"test_results_{int(time.time())}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Kapsamlı test tamamlandı")
        logger.info(f"Sonuçlar: {json_file}")
        logger.info(f"Rapor: {report_file}")
        
        return {
            'results': results,
            'pgn_file': pgn_file,
            'report_file': report_file,
            'chart_files': chart_files,
            'json_file': json_file
        }
    
    def run_automated_testing_cycle(self, target_engine: str = "stockfish", 
                                  cycles: int = 5) -> List[Dict]:
        """Otomatik test döngüsü"""
        all_results = []
        
        for cycle in range(cycles):
            logger.info(f"Test döngüsü {cycle + 1}/{cycles} başlatılıyor")
            
            try:
                # Test çalıştır
                cycle_results = self.run_comprehensive_test(
                    target_engine, 
                    "our_bot", 
                    games=50  # Daha az oyun ile hızlı test
                )
                
                all_results.append(cycle_results)
                
                # Sonuçları değerlendir
                win_rate = cycle_results['results']['engine1_win_rate']
                logger.info(f"Döngü {cycle + 1} sonucu: {win_rate:.2%} kazanma oranı")
                
                # Başarı kriteri kontrolü
                if win_rate < 0.4:  # %40'ın altında kazanma oranı
                    logger.info("Hedef başarıya ulaşıldı!")
                    break
                
                # Döngüler arası bekleme
                if cycle < cycles - 1:
                    logger.info("Sonraki döngü için bekleniyor...")
                    time.sleep(60)  # 1 dakika bekle
                
            except Exception as e:
                logger.error(f"Döngü {cycle + 1} hatası: {e}")
                continue
        
        return all_results


def main():
    """Ana test fonksiyonu"""
    # Logging ayarla
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test sistemi oluştur
    tester = TestEngine()
    
    # Basit test çalıştır
    try:
        results = tester.run_comprehensive_test("stockfish", "our_bot", games=20)
        print(f"Test tamamlandı! Kazanma oranı: {results['results']['engine1_win_rate']:.2%}")
    except Exception as e:
        print(f"Test hatası: {e}")


if __name__ == "__main__":
    main()
