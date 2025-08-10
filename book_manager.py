"""
Açılış Kitabı Yöneticisi - PGN'lerden Polyglot kitap oluşturma ve yönetimi
"""

import chess
import chess.pgn
import chess.polyglot
import logging
import subprocess
import random
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import pandas as pd

import config

logger = logging.getLogger(__name__)

class BookManager:
    """Açılış kitabı oluşturma ve yönetimi"""
    
    def __init__(self):
        self.pgn_dir = config.PGN_DIR
        self.books_dir = config.BOOKS_DIR
        self.filter_criteria = config.FILTER_CRITERIA
        
    def download_pgn_data(self, urls: List[str] = None) -> List[Path]:
        """PGN verilerini indir"""
        if urls is None:
            urls = config.PGN_SOURCES
        
        downloaded_files = []
        
        for url in urls:
            try:
                filename = url.split('/')[-1]
                file_path = self.pgn_dir / filename
                
                if not file_path.exists():
                    logger.info(f"PGN indiriliyor: {url}")
                    subprocess.run(['wget', '-O', str(file_path), url], check=True)
                
                downloaded_files.append(file_path)
                logger.info(f"PGN indirildi: {file_path}")
                
            except Exception as e:
                logger.error(f"PGN indirme hatası {url}: {e}")
        
        return downloaded_files
    
    def extract_games_from_pgn(self, pgn_file: Path, max_games: int = None) -> List[chess.pgn.Game]:
        """PGN dosyasından oyunları çıkar"""
        games = []
        
        try:
            with open(pgn_file, 'r', encoding='utf-8') as f:
                game_count = 0
                
                while True:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        
                        if self._filter_game(game):
                            games.append(game)
                            game_count += 1
                            
                            if max_games and game_count >= max_games:
                                break
                                
                    except Exception as e:
                        logger.debug(f"Oyun okuma hatası: {e}")
                        continue
            
            logger.info(f"{len(games)} oyun çıkarıldı: {pgn_file}")
            
        except Exception as e:
            logger.error(f"PGN okuma hatası {pgn_file}: {e}")
        
        return games
    
    def _filter_game(self, game: chess.pgn.Game) -> bool:
        """Oyunu filtreleme kriterlerine göre kontrol et"""
        try:
            # Sonuç kontrolü
            result = game.headers.get("Result", "")
            if result != self.filter_criteria["result_filter"]:
                return False
            
            # Rating kontrolü
            white_rating = game.headers.get("WhiteElo", "0")
            black_rating = game.headers.get("BlackElo", "0")
            
            try:
                white_rating = int(white_rating)
                black_rating = int(black_rating)
            except ValueError:
                return False
            
            min_rating = self.filter_criteria["min_rating"]
            max_rating = self.filter_criteria["max_rating"]
            
            if not (min_rating <= white_rating <= max_rating and 
                   min_rating <= black_rating <= max_rating):
                return False
            
            # ECO kodu kontrolü (opsiyonel)
            eco_codes = self.filter_criteria.get("eco_codes", [])
            if eco_codes:
                eco = game.headers.get("ECO", "")
                if eco not in eco_codes:
                    return False
            
            # Oyun uzunluğu kontrolü
            move_count = len(list(game.mainline_moves()))
            if move_count < 10 or move_count > 200:
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Oyun filtreleme hatası: {e}")
            return False
    
    def analyze_opening_variations(self, games: List[chess.pgn.Game]) -> Dict[str, Dict]:
        """Açılış varyantlarını analiz et"""
        variations = defaultdict(lambda: {
            'games': [],
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'total_moves': 0
        })
        
        for game in games:
            try:
                # İlk 10 hamleyi al
                board = game.board()
                moves = list(game.mainline_moves())
                
                if len(moves) < 5:
                    continue
                
                # Açılış pozisyonunu oluştur
                opening_moves = moves[:10]
                opening_fen = board.fen()
                
                for i, move in enumerate(opening_moves):
                    if i >= 10:
                        break
                    
                    # Pozisyonu FEN olarak kaydet
                    fen = board.fen()
                    san_move = board.san(move)
                    
                    variation_key = f"{fen}:{san_move}"
                    
                    variations[variation_key]['games'].append(game)
                    variations[variation_key]['total_moves'] += 1
                    
                    # Sonuç analizi
                    result = game.headers.get("Result", "")
                    if result == "1-0":
                        variations[variation_key]['wins'] += 1
                    elif result == "1/2-1/2":
                        variations[variation_key]['draws'] += 1
                    elif result == "0-1":
                        variations[variation_key]['losses'] += 1
                    
                    board.push(move)
                
            except Exception as e:
                logger.debug(f"Varyant analiz hatası: {e}")
                continue
        
        # İstatistikleri hesapla
        for key, data in variations.items():
            total_games = len(data['games'])
            if total_games > 0:
                data['win_rate'] = data['wins'] / total_games
                data['draw_rate'] = data['draws'] / total_games
                data['loss_rate'] = data['losses'] / total_games
                data['avg_moves'] = data['total_moves'] / total_games
        
        return dict(variations)
    
    def create_polyglot_book(self, games: List[chess.pgn.Game], 
                           output_file: str = None,
                           min_games: int = 5,
                           min_win_rate: float = 0.6) -> Path:
        """Polyglot kitap oluştur"""
        if output_file is None:
            output_file = config.BOOK_CONFIG["default_book"]
        
        output_path = self.books_dir / output_file
        
        try:
            # Geçici PGN dosyası oluştur
            temp_pgn = self.pgn_dir / "temp_filtered.pgn"
            
            with open(temp_pgn, 'w', encoding='utf-8') as f:
                for game in games:
                    f.write(str(game) + "\n\n")
            
            # Polyglot komutunu çalıştır
            cmd = [
                'polyglot', 'make-book',
                '-pgn', str(temp_pgn),
                '-bin', str(output_path),
                '-min-game', str(min_games),
                '-max-ply', '20',  # İlk 20 hamle
                '-min-score', '0',  # Minimum skor
                '-max-score', '100'  # Maksimum skor
            ]
            
            logger.info(f"Polyglot kitap oluşturuluyor: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Kitap oluşturuldu: {output_path}")
            
            # Geçici dosyayı sil
            temp_pgn.unlink()
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Polyglot hatası: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Kitap oluşturma hatası: {e}")
            raise
    
    def optimize_book_weights(self, book_path: Path, 
                            target_win_rate: float = 0.7) -> Path:
        """Kitap ağırlıklarını optimize et"""
        try:
            # Mevcut kitabı oku
            reader = chess.polyglot.open_reader(book_path)
            
            # Yeni kitap oluştur
            optimized_path = book_path.parent / f"optimized_{book_path.name}"
            
            with open(optimized_path, 'wb') as f:
                for entry in reader:
                    # Ağırlığı optimize et
                    optimized_weight = self._optimize_weight(entry.weight, target_win_rate)
                    
                    # Yeni entry yaz
                    f.write(entry.key.to_bytes(8, 'big'))
                    f.write(entry.move.to_bytes(2, 'big'))
                    f.write(optimized_weight.to_bytes(2, 'big'))
                    f.write(entry.learn.to_bytes(4, 'big'))
            
            reader.close()
            logger.info(f"Kitap optimize edildi: {optimized_path}")
            
            return optimized_path
            
        except Exception as e:
            logger.error(f"Kitap optimizasyon hatası: {e}")
            raise
    
    def _optimize_weight(self, current_weight: int, target_win_rate: float) -> int:
        """Ağırlığı optimize et"""
        # Basit optimizasyon: hedef kazanma oranına göre ağırlığı ayarla
        min_weight = config.BOOK_CONFIG["min_weight"]
        max_weight = config.BOOK_CONFIG["max_weight"]
        
        # Ağırlığı hedef orana göre ayarla
        optimized_weight = int(current_weight * target_win_rate)
        
        # Sınırlar içinde tut
        optimized_weight = max(min_weight, min(max_weight, optimized_weight))
        
        return optimized_weight
    
    def merge_books(self, book_paths: List[Path], output_path: Path) -> Path:
        """Birden fazla kitabı birleştir"""
        try:
            merged_entries = {}
            
            for book_path in book_paths:
                if not book_path.exists():
                    continue
                
                reader = chess.polyglot.open_reader(book_path)
                
                for entry in reader:
                    key = (entry.key, entry.move)
                    
                    if key in merged_entries:
                        # Ağırlıkları topla
                        merged_entries[key] = chess.polyglot.PolyglotEntry(
                            key=entry.key,
                            move=entry.move,
                            weight=merged_entries[key].weight + entry.weight,
                            learn=entry.learn
                        )
                    else:
                        merged_entries[key] = entry
                
                reader.close()
            
            # Birleştirilmiş kitabı yaz
            with open(output_path, 'wb') as f:
                for entry in merged_entries.values():
                    f.write(entry.key.to_bytes(8, 'big'))
                    f.write(entry.move.to_bytes(2, 'big'))
                    f.write(entry.weight.to_bytes(2, 'big'))
                    f.write(entry.learn.to_bytes(4, 'big'))
            
            logger.info(f"Kitaplar birleştirildi: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Kitap birleştirme hatası: {e}")
            raise
    
    def analyze_book_performance(self, book_path: Path, 
                               test_games: int = 100) -> Dict[str, float]:
        """Kitap performansını analiz et"""
        try:
            reader = chess.polyglot.open_reader(book_path)
            
            total_entries = 0
            total_weight = 0
            move_distribution = defaultdict(int)
            
            for entry in reader:
                total_entries += 1
                total_weight += entry.weight
                move_distribution[entry.move.uci()] += 1
            
            reader.close()
            
            # İstatistikleri hesapla
            avg_weight = total_weight / total_entries if total_entries > 0 else 0
            
            # En popüler hamleleri bul
            popular_moves = sorted(move_distribution.items(), 
                                 key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_entries': total_entries,
                'average_weight': avg_weight,
                'popular_moves': popular_moves,
                'coverage_estimate': min(1.0, total_entries / 1000)  # Tahmini kapsama
            }
            
        except Exception as e:
            logger.error(f"Kitap analiz hatası: {e}")
            return {}
    
    def create_anti_stockfish_book(self, pgn_files: List[Path] = None) -> Path:
        """Stockfish'e karşı özel kitap oluştur"""
        if pgn_files is None:
            pgn_files = list(self.pgn_dir.glob("*.pgn"))
        
        logger.info("Anti-Stockfish kitap oluşturuluyor...")
        
        # Tüm oyunları topla
        all_games = []
        for pgn_file in pgn_files:
            games = self.extract_games_from_pgn(pgn_file, max_games=1000)
            all_games.extend(games)
        
        logger.info(f"Toplam {len(all_games)} oyun toplandı")
        
        # Varyantları analiz et
        variations = self.analyze_opening_variations(all_games)
        
        # Yüksek kazanma oranına sahip varyantları filtrele
        good_variations = {
            k: v for k, v in variations.items()
            if v.get('win_rate', 0) >= 0.6 and len(v['games']) >= 5
        }
        
        logger.info(f"{len(good_variations)} iyi varyant bulundu")
        
        # Bu varyantlardan oyunları topla
        selected_games = []
        for variation_data in good_variations.values():
            selected_games.extend(variation_data['games'])
        
        # Tekrarları kaldır
        selected_games = list(set(selected_games))
        
        # Kitap oluştur
        book_path = self.create_polyglot_book(
            selected_games,
            output_file="anti_stockfish.bin",
            min_games=3,
            min_win_rate=0.6
        )
        
        # Performans analizi
        performance = self.analyze_book_performance(book_path)
        logger.info(f"Kitap performansı: {performance}")
        
        return book_path
    
    def backup_book(self, book_path: Path) -> Path:
        """Kitabı yedekle"""
        backup_path = book_path.parent / f"backup_{book_path.name}"
        
        try:
            import shutil
            shutil.copy2(book_path, backup_path)
            logger.info(f"Kitap yedeklendi: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Kitap yedekleme hatası: {e}")
            raise
