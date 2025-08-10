#!/bin/bash

# Santranç Bot Kurulum Scripti
# Bu script gerekli tüm bileşenleri kurar

set -e  # Hata durumunda dur

echo "🎯 Santranç Bot Kurulum Scripti"
echo "================================"

# Sistem kontrolü
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✅ Linux sistemi tespit edildi"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ macOS sistemi tespit edildi"
else
    echo "❌ Desteklenmeyen işletim sistemi: $OSTYPE"
    exit 1
fi

# Python kontrolü
if command -v python3 &> /dev/null; then
    echo "✅ Python3 bulundu"
    python3 --version
else
    echo "❌ Python3 bulunamadı. Lütfen Python3 kurun."
    exit 1
fi

# pip kontrolü
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 bulundu"
else
    echo "❌ pip3 bulunamadı. Lütfen pip3 kurun."
    exit 1
fi

# Gerekli sistem paketlerini kur
echo ""
echo "📦 Sistem paketleri kuruluyor..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pip git build-essential wget curl
        echo "✅ Sistem paketleri kuruldu"
    else
        echo "⚠️  apt-get bulunamadı. Manuel kurulum gerekebilir."
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew update
        brew install python3 git wget curl
        echo "✅ Sistem paketleri kuruldu"
    else
        echo "⚠️  Homebrew bulunamadı. Manuel kurulum gerekebilir."
    fi
fi

# Python bağımlılıklarını kur
echo ""
echo "🐍 Python bağımlılıkları kuruluyor..."
pip3 install -r requirements.txt
echo "✅ Python bağımlılıkları kuruldu"

# Dizinleri oluştur
echo ""
echo "📁 Dizinler oluşturuluyor..."
mkdir -p data/books data/pgn data/tablebases logs test_results
echo "✅ Dizinler oluşturuldu"

# Stockfish kurulumu
echo ""
echo "🐟 Stockfish kuruluyor..."

if command -v stockfish &> /dev/null; then
    echo "✅ Stockfish zaten kurulu"
    stockfish --version
else
    echo "📥 Stockfish indiriliyor..."
    
    # Geçici dizin oluştur
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Stockfish'i klonla
    git clone https://github.com/official-stockfish/Stockfish.git
    cd Stockfish/src
    
    # Derle
    echo "🔨 Stockfish derleniyor..."
    make build ARCH=x86-64
    
    # Kur
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo cp stockfish /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        sudo cp stockfish /usr/local/bin/
    fi
    
    # Temizlik
    cd /
    rm -rf "$TEMP_DIR"
    
    echo "✅ Stockfish kuruldu"
fi

# Cutechess-cli kurulumu
echo ""
echo "🎮 Cutechess-cli kuruluyor..."

if command -v cutechess-cli &> /dev/null; then
    echo "✅ Cutechess-cli zaten kurulu"
else
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y cutechess-cli
        else
            echo "⚠️  Cutechess-cli manuel kurulum gerekebilir"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install cutechess-cli
        else
            echo "⚠️  Cutechess-cli manuel kurulum gerekebilir"
        fi
    fi
fi

# Polyglot kurulumu
echo ""
echo "📚 Polyglot kuruluyor..."

if command -v polyglot &> /dev/null; then
    echo "✅ Polyglot zaten kurulu"
else
    echo "📥 Polyglot indiriliyor..."
    
    # Geçici dizin oluştur
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Polyglot'u indir
    wget https://github.com/official-stockfish/polyglot/releases/download/2.0.4/polyglot-2.0.4.tar.gz
    tar -xzf polyglot-2.0.4.tar.gz
    cd polyglot-2.0.4
    
    # Derle
    echo "🔨 Polyglot derleniyor..."
    make
    
    # Kur
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo cp polyglot /usr/local/bin/
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        sudo cp polyglot /usr/local/bin/
    fi
    
    # Temizlik
    cd /
    rm -rf "$TEMP_DIR"
    
    echo "✅ Polyglot kuruldu"
fi

# Syzygy tablebase indirme (opsiyonel)
echo ""
echo "🗄️  Syzygy tablebase indiriliyor (opsiyonel)..."

TABLEBASE_DIR="data/tablebases"
if [ ! -d "$TABLEBASE_DIR" ]; then
    mkdir -p "$TABLEBASE_DIR"
fi

# 3-4-5 taşlı tablebase'leri indir
echo "📥 3-4-5 taşlı tablebase'ler indiriliyor..."
cd "$TABLEBASE_DIR"

# Küçük tablebase'ler (test için)
wget -O 3-4-5.zip "https://tablebase.lichess.ovh/tables/standard/3-4-5.zip" || echo "⚠️  Tablebase indirme başarısız"

if [ -f "3-4-5.zip" ]; then
    unzip -o 3-4-5.zip || echo "⚠️  Tablebase çıkarma başarısız"
    rm 3-4-5.zip
    echo "✅ Tablebase'ler indirildi"
else
    echo "⚠️  Tablebase indirilemedi. Manuel indirme gerekebilir."
fi

cd - > /dev/null

# Test çalıştır
echo ""
echo "🧪 Sistem testi yapılıyor..."

# Python modüllerini test et
python3 -c "import chess; print('✅ python-chess çalışıyor')" || echo "❌ python-chess hatası"

# Stockfish'i test et
if command -v stockfish &> /dev/null; then
    echo "✅ Stockfish test ediliyor..."
    echo "quit" | stockfish > /dev/null 2>&1 && echo "✅ Stockfish çalışıyor" || echo "❌ Stockfish hatası"
fi

# Cutechess-cli'yi test et
if command -v cutechess-cli &> /dev/null; then
    echo "✅ Cutechess-cli test ediliyor..."
    cutechess-cli --help > /dev/null 2>&1 && echo "✅ Cutechess-cli çalışıyor" || echo "❌ Cutechess-cli hatası"
fi

# Polyglot'u test et
if command -v polyglot &> /dev/null; then
    echo "✅ Polyglot test ediliyor..."
    polyglot --help > /dev/null 2>&1 && echo "✅ Polyglot çalışıyor" || echo "❌ Polyglot hatası"
fi

echo ""
echo "🎉 Kurulum tamamlandı!"
echo "======================"
echo ""
echo "Kullanım:"
echo "  python3 main.py --hybrid          # Hibrit motor ile çalıştır"
echo "  python3 test_hybrid.py            # Hibrit motor testi"
echo "  python3 test_engine.py            # Genel test"
echo ""
echo "Daha fazla bilgi için README.md dosyasını okuyun."
echo ""
echo "İyi oyunlar! 🏆"
