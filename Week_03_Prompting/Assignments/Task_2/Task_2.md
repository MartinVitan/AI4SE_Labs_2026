# Task 2 Assignment

Solve the problem defined for this task using the selected prompts from Task 1. Store all outputs. Also create a brief report comparing how well the model solved these problems with different prompting techniques that will also contain a nice vizualisation. Make sure to measure inference times.

HINTS:
Start new session for each compared prompt.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 1b

OUTPUT:
A data file or files containing the problem solutions (predictions) obtained by different prompts, with model and prompt identification metadata
A brief report on how well the model completed the problems with different prompts

Odpovede obsahujú  SQL kódové bloky s dopytmi.
1. prompt RACE : completion time 3m 12s (model: gpt-6-luna) = RACEout.txt

2. prompt RTF : completion time 2m 32s (model: gpt-6-luna) = RTFout.txt

3. prompt CO-STAR : completion time 2m 35s (model: gpt-6-luna) = COSTARout.txt

- RACE: 135/155 (87,10 %)
- RTF: 127/155 (81,94 %)
- CO-STAR: 136/155 (87,74 %)

Evaluátor som upravil preto, že referencia napríklad očakáva `portola park`
s ID `3`, zatiaľ čo databáza eviduje rovnaký názov pod ID `2633`. Pôvodné
porovnanie dvojice `(ID, názov)` označilo výsledok za nesprávny, aj keď
názov reštaurácie bol korektný. Upravený evaluátor naďalej spúšťa predikované SQL
nad dodanou databázou, ale pri skórovaní porovnáva presné názvy a ID ignoruje.

Texty promptov obsahujú vložený CSV vrátane stĺpca `result`, hoci model dostal pokyn tento stĺpec nepoužívať.

Samotné výstupy modelov nie sú sfalšované ani nijak upravené.