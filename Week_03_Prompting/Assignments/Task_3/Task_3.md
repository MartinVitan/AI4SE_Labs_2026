# Task 3 Assignment

Propose another metric for assessing how well the problem was completed. Argue and defend why it is a good and applicable metric for the problem. Invention and originality is appreciated. Discuss if the metric complements or replaces the original metric(s) of the problem. Implement the metric calculation, and calculate the metric values for existing predictions from Task 2. Create a report comparing the metric values for different prompts.

POINTS AWARDED FOR SUCCESSFUL COMPLETION: 1b

OUTPUT:
A source code file or files containing the metric implementation
A report on how well in terms of the new metric the model completed the problems with different prompts

ALTERNATIVE OUTPUT:
If the metric is not possible to calculate, create a detailed guide on how to implement and calculate it.

V Task 2 som už porovnával názvy reštaurácií a ignoroval ID. V Task 3
chcem merať aj čiastočne správne odpovede.

Pre každú otázku sa počíta hodnota F1:

True positive = názov je v referencii aj v predikcii (správne nájdené reštaurácie)
False positive = názov v referencií nie je ale v predikcií áno (nesprávne pridaná reštaurácia)
False negative = názov je v referencii, ale nie v  predikcií (vynechaná reštaurácia, ktorú model mal nájsť)

Presnosť = TP / (TP + FP) - podiel správnych vrátených názvov v odpovedi modelu
Úplnosť = TP / (TP + FN) - podiel očakávaných názvov nájdených modelom
F1 = 2 * Presnosť * Úplnosť / (Presnosť + Úplnosť) #spoločné skóre - zohľadňuje nesprávne pridané a vynechané reštaurácie, táto metrika len dopĺňa pôvodnú metriku

obe odpovede prázdne = F1 = 100 %

Napríklad ak referencia očakáva A, B, C a model vráti A, B, C, D:

Presnosť: 3 zo 4 vrátených názvov je správnych 75%
Úplnosť: našiel všetky 3 očakávané názvy 100%

V tomto vyhodnotení obe vlastnosti majú rovnakú váhu. Následne F1 zo všetkých otázok spriemerujem. Poradie reštaurácií ignorujem.

RACE: priemerné F1 96,76 %
RTF: priemerné F1 90,02 %
CO-STAR: priemerné F1 95,30 %