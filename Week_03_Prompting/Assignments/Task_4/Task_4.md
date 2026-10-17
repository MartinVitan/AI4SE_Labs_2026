# Task 4 Assignment

Reiterate on the prompt comparison from Tasks 2 and 3. Make a detailed analysis on the metric values obtained by different prompts. Create tables and graphs demonstrating the obtained results. Determine, if the difference between the prompts is statistically significant. Explain, why the differences between prompts are the way it is. Consider the prompts, the model, and the coding agent as factors.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 2b

OUTPUT:
A detailed report comparing the prompts and providing interpretation of results

| Framework | Presná zhoda (Task 2) | Priemerné F1 (Task 3) | Čas generovania |
|---|---:|---:|---:|
| RACE | 135/155 (87,10 %) | 96,76 % | 3 min 12 s |
| RTF | 127/155 (81,94 %) | 90,02 % | 2 min 32 s |
| CO-STAR | 136/155 (87,74 %) | 95,30 % | 2 min 35 s |

CO-STAR dosiahol najvyššiu presnú zhodu: 87,74 %, čo je o 0,64 percentuálneho bodu viac ako RACE. RACE mal najvyššie priemerné F1: 96,76 %, teda o 1,46 bodu viac ako CO-STAR. RTF dosiahol najnižšiu presnú zhodu aj F1, ale odpovede vytvoril najrýchlejšie.

Na posúdenie, či rozdiely medzi frameworkmi mohli vzniknúť náhodou, sa vypočítali p-hodnoty. Výsledky sa porovnávali na tých istých otázkach. Pre presnú zhodu sa použil McNemarov test, ktorý porovnáva otázky, pri ktorých sa frameworky nezhodli v tom, či odpovedali správne. Pre F1 sa použil párový Wilcoxonov test, ktorý porovnáva F1 skóre oboch frameworkov pri každej otázke. Keďže sa porovnávajú tri dvojice, Holmova metóda upravuje p-hodnoty a znižuje riziko, že viac testov náhodne ukáže významný rozdiel.

Ak je upravená p-hodnota menšia ako 0,05, rozdiel označujem za štatisticky významný.

| Porovnanie | Presná zhoda: upravené p | Významný rozdiel? | F1: upravené p | Významný rozdiel? |
|---|---:|---|---:|---|
| RACE – RTF | 0,115 | Nie | 0,004 | Áno |
| RACE – CO-STAR | 1,000 | Nie | 0,212 | Nie |
| RTF – CO-STAR | 0,105 | Nie | 0,011 | Áno |
