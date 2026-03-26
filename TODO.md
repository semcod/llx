
zrób refaktoryzacje examples, preferuję komendy w bash niż implementacje llx jako kod python , jeśli to potrzebne to prznieś kod i logikę z examples/*/*.py do biblioteki llx, chodzi o to by zminimaliziwoać ilość kodu potrzebnego do wdrożenia llx w różnych użyciach, aby była to łatwa w użyciu biblitoeka
uruchom kazdy przyklad i sparwdz czy porpawnie uzywa LLM free

Rozbuduj Rozszerzenie CLI llx
Czyste Bashowe przykłady: Wszystkie katalogi w examples/ używają teraz bezpośrednich, łatwych do zrozumienia skryptów run.sh, korzystających bezpośrednio z programu llx, co znacznie minimalizuje próg wejścia w to narzędzie.
Usunięcie skryptów Pythona: Kody i logika z examples/*/*.py zostały usunięte.