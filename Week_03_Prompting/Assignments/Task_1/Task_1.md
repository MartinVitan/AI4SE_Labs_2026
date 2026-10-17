# Task 1 Assignment

Choose 3 prompting frameworks (such as ROSES) from this https://frompting.com/frameworks or other website. Do not use ROSES nor zero-shot propting. Formulate prompts based on each chosen framework, that will later be used to solve problems in Task 2. Explain why you chose each of the prompts, what do you expect from it.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 1b

OUTPUT:
A data file or files containing the formulated prompts
A report on why each prompt framework was chosen and where was it found



Musím zvoliť také frameworky, ktoré dokážu pracovať s kontextom, viem im špecifikovať cieľ úlohy a formát výstupu.

1. framework : RACE (Role, Action, Context and Expectation) = promptRACE.txt
Source : https://frompting.com/frameworks/race

Viem jasne zadefinovať modelu s akými dátami má pracovať (časť CONTEXT) a v časti EXPECTATION viem modelu explicitne povedať aký output odneho očakávam v akom presnom formáte SQL dopytu.

2. framework : RTF (Role, Task and Format) = promptRTF.txt
Source : https://frompting.com/frameworks/rtf

Vysvetľuje, kto má model byť, čo má urobiť a ako má odpovedať. Očakávam, že model vytvorí SQL dotazy podľa zadanej úlohy a databázovej schémy a vráti ich v jednotnom formáte.

3. framework : CO-STAR (Context, Objective, Style, Tone, Audience and Response format) = promptCOSTAR.txt
Source : https://frompting.com/frameworks/co-star

CO-STAR mi umožňuje podrobne opísať kontext databázy, cieľ úlohy a požadovaný formát odpovede. Očakávam že CSV súbor s SQL dotazmi podľa priloženej schémy bude možné jednoducho automaticky vyhodnotiť.