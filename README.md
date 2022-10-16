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


## 最適化

### テオ・ヤンセン機構

SciPyの最適化ツールとSymPyの符号計算でテオ・ヤンセン機構の動きを計算します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=optimize%2Frobot_walk.ipynb

![テオ・ヤンセン機構](images/linkage.png)

## 描画

### ジュリア集合

高速演算のWASMファイルをcffiでロードし、Pythonから呼び出し、ジュリア集合のリアルタイム計算を実現しました。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Fjulia_set.ipynb

![ジュリア集合](images/julia.gif)

### L-System

文字列の入れ替えでフラクタルを描画します。

https://ruoyu0088.github.io/jupyterlite_demos/lab?path=plots%2Flsystem.ipynb

![L-System](images/lsystem.png)

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