# ベースイメージとしてapemill/pyinstaller-windowsを使用
FROM apemill/pyinstaller-windows

# 作業ディレクトリを設定
WORKDIR /src

# ホスト側のファイルをコンテナにコピー
COPY . .

# パッケージをインストール
RUN pip install /src/python_rtmidi-1.5.5-cp311-cp311-win_amd64.whl

# pyinstallerでexeファイルを作成
RUN pyinstaller /src/main.spec --clean

# exeファイルを/srcに移動
RUN mv dist/main.exe /src/main.exe

# 不要なファイルを削除
RUN rm -rf __pycache__/ build/ dist/
