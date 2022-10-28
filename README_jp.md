[![en](https://img.shields.io/badge/lang-English-red.svg)](https://github.com/ruoyu0088/jupyterlite_demos/blob/main/README.md)
[![cn](https://img.shields.io/badge/lang-Chinese-green.svg)](https://github.com/ruoyu0088/jupyterlite_demos/blob/main/README_cn.md)
[![jp](https://img.shields.io/badge/lang-Japanese-yellow.svg)](https://github.com/ruoyu0088/jupyterlite_demos/blob/main/README_jp.md)

# ウェブブラウザで動くPython開発環境JupyterLiteのデモ

このデモはJupyterLiteをGitHub Pagesに配備した静的サイトです。 Firefox 90+或いはChromium 89+で次のリンクを開いてください。

**https://ruoyu0088.github.io/jupyterlite_demos/lab/index.html**

自分のJupyterLiteサイトを作るには次のリンクに参考してください。

https://jupyterlite.readthedocs.io/en/latest/quickstart/deploy.html

# デモ一覧

## PySATを利用したパズルソルバー

PySATでいろいろなパズルを解きます。

### 数独

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fsudoku_solver.ipynb

![数独ソルバー](images/sudoku.png)

### 四角に切れ

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fshikaku_solver.ipynb

![四角に切れ](images/shikaku.png)

### お絵かきロジック

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fnonogram_solver.ipynb

![お絵かきロジック](images/nonogram.png)

### ナンバーリンク

ナンバーリンクは、盤面にある同じ数字同士を線でつなぐペンシルパズルです。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fnumber_link.ipynb

![ナンバーリンク](images/number_link.png)


### スリザーリンク

スリザーリンク（英: Slitherlink）は格子点の間に記された数字を頼りに、格子点の間を水平な線分（横線）または垂直な線分（縦線）で結び、盤面に一つの閉じた輪（単一閉曲線）を書き上げるペンシルパズルの一種である。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fslitherlink.ipynb

![](images/slitherLink.png)

### 3D磁石キューブパズル

次のような3D磁石キューブパズルを解けます。

![](images/magnetcube.jpg)

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=pysat%2Fmagnetcube.ipynb

![](images/magnetcube.png)

## 最適化

### テオ・ヤンセン機構

SciPyの最適化ツールとSymPyの符号計算でテオ・ヤンセン機構の動きを計算します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=optimize%2Frobot_walk.ipynb

![テオ・ヤンセン機構](images/linkage.png)

### 蟻コロニーで巡回セールスマン問題を解く

各都市を1回訪れて最初の都市に戻る最短ルートを求める問題です。これはNP困難な問題であり、この例ではアリのコロニー アルゴリズムを使用して、問題の近似最適解を計算します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=optimize%2Fant-colony-salesman.ipynb

![巡回セールスマン問題](images/salesman.gif)

## 描画

### ジュリア集合

高速演算のWASMファイルをcffiでロードし、Pythonから呼び出し、ジュリア集合のリアルタイム計算を実現しました。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Fjulia_set.ipynb

![ジュリア集合](images/julia.gif)

### L-System

文字列の入れ替えでフラクタルを描画します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Flsystem.ipynb

![L-System](images/lsystem.png)

### 反復関数系フラクタル

複数の三角形からフラクタルを描画します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Fifs.ipynb

![IFS](images/ifs.png)

### バラの花

Plotlyの3D描画機能でバラの花を作りました。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Fplots_01.ipynb

![バラの花](images/rose.png)

### Prime Climb

[Prime Climb](https://mathforlove.com/games/prime-climb/)は掛け算や因数分解などを勉強するための算数ゲームです。このNotebookはBokehを使ってPrime Climbのゲームボードを描画します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Fprime_climb_draw.ipynb

![prime climb](images/prime_climb.png)

## Graph

### 箱入り娘パズル

SciPyの最短パス計算関数`dijkstra()`を利用して、箱入り娘パズルの最短解を求めます。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=graph%2Fklotski_solver.ipynb

![箱入り娘パズル](images/klotski.png)

## Simulation

### 蟻群

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=simulation%2Fants.ipynb

![蟻群](images/ants.gif)

### Particle Life

粒子の間に重力と反重力を加え、運動方程式で位置を計算すると、面白い動きになりました。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=simulation%2Fparticle_life.ipynb

![Particle Life](images/particle_life.gif)

## 幾何学

### 平面幾何学スクリプト

SolveSpaceの幾何学エンジンを使った幾何学のスクリプトです。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=geometry%2Fgeometry_script.ipynb

![幾何学スクリプト](images/geometry_script.png)

### Strandbeest歩くロボット

SolveSpaceを使った幾何学のスクリプトで歩くロボットのアニメーションを作成しました。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=geometry%2Fstrandbeest_walk.ipynb

![Strandbeest歩くロボット](images/strandbeest_walk.gif)

## 制御

### N重振り子制御

SymPyでN重振り子の運動方程式を導出し、線形化させ、SciPyで制御ゲインの計算とODEソルバーでフィードバック制御をシミュレーションします。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=control%2Fpendulum_control.ipynb

![N-pendulum](images/N-pendulum.gif)