"""
Motor Wrapper - Çoklu motor desteği ve tablebase entegrasyonu
"""

import chess
import chess.engine
import chess.polyglot
import chess.syzygy
import logging
import random
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

import config

logger = logging.getLogger(__name__)

class EngineWrapper:
    """Çoklu motor desteği ve tablebase entegrasyonu ile motor wrapper"""
    
    def __init__(self, engine_name: str = "stockfish"):
        self.engine_name = engine_name
        self.engine = None
        self.tablebase = None
        self.book = None
        self.engine_info = config.ENGINES.get(engine_name, {})
        
        self._initialize_engine()
        self._initialize_tablebase()
        self._initialize_book()
    
    def _initialize_engine(self):
        """Motoru başlat ve ayarları yapılandır"""
        try:
            engine_path = self.engine_info.get("path")
            if not engine_path or not Path(engine_path).exists():
                logger.error(f"Motor bulunamadı: {engine_path}")
                return
            
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            
            # Motor ayarlarını yapılandır
            options = self.engine_info.get("options", {})
            for option, value in options.items():
                try:
                    self.engine.configure({option: value})
                    logger.info(f"Motor ayarı: {option} = {value}")
                except Exception as e:
                    logger.warning(f"Motor ayarı yapılamadı {option}: {e}")
            
            # Gelişmiş ayarları uygula
            advanced_options = config.ADVANCED_ENGINE_CONFIG
            for option, value in advanced_options.items():
                try:
                    self.engine.configure({option: value})
                except Exception as e:
                    logger.debug(f"Gelişmiş ayar yapılamadı {option}: {e}")
            
            logger.info(f"Motor başlatıldı: {self.engine_name}")
            
        except Exception as e:
            logger.error(f"Motor başlatılamadı: {e}")
            self.engine = None
    
    def _initialize_tablebase(self):
        """Syzygy tablebase'i başlat"""
        if not config.SYZYGY_CONFIG["enabled"]:
            return
        
        try:
            tablebase_path = config.SYZYGY_CONFIG["path"]
            if Path(tablebase_path).exists():
                self.tablebase = chess.syzygy.open_tablebase(tablebase_path)
                logger.info(f"Tablebase başlatıldı: {tablebase_path}")
            else:
                logger.warning(f"Tablebase dizini bulunamadı: {tablebase_path}")
        except Exception as e:
            logger.error(f"Tablebase başlatılamadı: {e}")
    
    def _initialize_book(self):
        """Açılış kitabını yükle"""
        try:
            book_path = config.get_book_path()
            if book_path.exists():
                self.book = chess.polyglot.open_reader(book_path)
                logger.info(f"Açılış kitabı yüklendi: {book_path}")
            else:
                logger.warning(f"Açılış kitabı bulunamadı: {book_path}")
        except Exception as e:
            logger.error(f"Açılış kitabı yüklenemedi: {e}")
    
    def get_move(self, board: chess.Board, time_limit: float = None) -> Optional[chess.Move]:
        """
        Verilen pozisyon için en iyi hamleyi döndür
        
        Öncelik sırası:
        1. Tablebase (6 taş veya daha az)
        2. Açılış kitabı (ilk hamlelerde)
        3. Motor analizi
        """
        if board.is_game_over():
            return None
        
        # 1. Tablebase kontrolü
        if self.tablebase and self._should_use_tablebase(board):
            move = self._get_tablebase_move(board)
            if move:
                logger.debug("Tablebase hamlesi kullanıldı")
                return move
        
        # 2. Açılış kitabı kontrolü
        if self.book and self._should_use_book(board):
            move = self._get_book_move(board)
            if move:
                logger.debug("Kitap hamlesi kullanıldı")
                return move
        
        # 3. Motor analizi
        if self.engine:
            move = self._get_engine_move(board, time_limit)
            if move:
                logger.debug("Motor hamlesi kullanıldı")
                return move
        
        return None
    
    def _should_use_tablebase(self, board: chess.Board) -> bool:
        """Tablebase kullanılmalı mı?"""
        if not self.tablebase:
            return False
        
        # Taş sayısını kontrol et
        piece_count = len(board.piece_map())
        probe_limit = config.SYZYGY_CONFIG["probe_limit"]
        
        return piece_count <= probe_limit
    
    def _get_tablebase_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Tablebase'den hamle al"""
        try:
            # Tablebase'den pozisyonu sorgula
            wdl = self.tablebase.probe_wdl(board)
            dtz = self.tablebase.probe_dtz(board)
            
            if wdl is None or dtz is None:
                return None
            
            # En iyi hamleyi bul
            best_move = None
            best_dtz = float('inf')
            
            for move in board.legal_moves:
                board.push(move)
                try:
                    move_dtz = self.tablebase.probe_dtz(board)
                    if move_dtz is not None and abs(move_dtz) < abs(best_dtz):
                        best_dtz = move_dtz
                        best_move = move
                except:
                    pass
                board.pop()
            
            return best_move
            
        except Exception as e:
            logger.debug(f"Tablebase hatası: {e}")
            return None
    
    def _should_use_book(self, board: chess.Board) -> bool:
        """Kitap kullanılmalı mı?"""
        if not self.book:
            return False
        
        # İlk hamlelerde ve belirli olasılıkla kullan
        move_number = len(board.move_stack)
        max_book_moves = config.BOOK_CONFIG["max_book_moves"]
        book_probability = config.GAME_CONFIG["book_probability"]
        
        return (move_number < max_book_moves and 
                random.random() < book_probability)
    
    def _get_book_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Kitaptan hamle al"""
        try:
            if not self.book:
                return None
            
            # Kitaptan ağırlıklı seçim yap
            entries = list(self.book.find_all(board))
            if not entries:
                return None
            
            # Ağırlıklara göre seçim yap
            total_weight = sum(entry.weight for entry in entries)
            if total_weight == 0:
                return random.choice(entries).move
            
            # Ağırlıklı rastgele seçim
            r = random.uniform(0, total_weight)
            cumulative_weight = 0
            
            for entry in entries:
                cumulative_weight += entry.weight
                if r <= cumulative_weight:
                    return entry.move
            
            return entries[0].move
            
        except Exception as e:
            logger.debug(f"Kitap hatası: {e}")
            return None
    
    def _get_engine_move(self, board: chess.Board, time_limit: float = None) -> Optional[chess.Move]:
        """Motordan hamle al"""
        try:
            if not self.engine:
                return None
            
            # Zaman limitini ayarla
            if time_limit is None:
                time_limit = config.GAME_CONFIG["engine_time_limit"]
            
            # Motor analizi
            result = self.engine.play(
                board,
                chess.engine.Limit(time=time_limit),
                info=chess.engine.INFO_SCORE | chess.engine.INFO_PV
            )
            
            return result.move
            
        except Exception as e:
            logger.error(f"Motor hatası: {e}")
            return None
    
    def analyze_position(self, board: chess.Board, depth: int = 20) -> Dict[str, Any]:
        """Pozisyonu analiz et"""
        try:
            if not self.engine:
                return {}
            
            result = self.engine.analyse(
                board,
                chess.engine.Limit(depth=depth),
                info=chess.engine.INFO_ALL
            )
            
            return {
                "score": result.get("score", None),
                "pv": result.get("pv", []),
                "depth": result.get("depth", 0),
                "nodes": result.get("nodes", 0),
                "time": result.get("time", 0)
            }
            
        except Exception as e:
            logger.error(f"Analiz hatası: {e}")
            return {}
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Motor bilgilerini döndür"""
        if not self.engine:
            return {}
        
        try:
            return self.engine.ping()
        except:
            return {}
    
    def close(self):
        """Motoru kapat"""
        try:
            if self.engine:
                self.engine.quit()
                logger.info("Motor kapatıldı")
        except Exception as e:
            logger.error(f"Motor kapatma hatası: {e}")
        
        try:
            if self.book:
                self.book.close()
                logger.info("Kitap kapatıldı")
        except Exception as e:
            logger.error(f"Kitap kapatma hatası: {e}")
        
        try:
            if self.tablebase:
                self.tablebase.close()
                logger.info("Tablebase kapatıldı")
        except Exception as e:
            logger.error(f"Tablebase kapatma hatası: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MultiEngineWrapper:
    """Çoklu motor desteği ile wrapper"""
    
    def __init__(self, engines: List[str] = None):
        self.engines = {}
        self.current_engine = None
        
        if engines is None:
            engines = ["stockfish"]
        
        for engine_name in engines:
            try:
                self.engines[engine_name] = EngineWrapper(engine_name)
                if self.current_engine is None:
                    self.current_engine = engine_name
            except Exception as e:
                logger.error(f"Motor yüklenemedi {engine_name}: {e}")
    
    def get_move(self, board: chess.Board, engine_name: str = None, **kwargs) -> Optional[chess.Move]:
        """Belirtilen motordan hamle al"""
        if engine_name is None:
            engine_name = self.current_engine
        
        if engine_name in self.engines:
            return self.engines[engine_name].get_move(board, **kwargs)
        
        return None
    
    def switch_engine(self, engine_name: str):
        """Aktif motoru değiştir"""
        if engine_name in self.engines:
            self.current_engine = engine_name
            logger.info(f"Aktif motor değiştirildi: {engine_name}")
        else:
            logger.warning(f"Motor bulunamadı: {engine_name}")
    
    def close(self):
        """Tüm motorları kapat"""
        for engine in self.engines.values():
            engine.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
