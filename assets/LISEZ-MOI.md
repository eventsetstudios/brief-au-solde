# assets/

Deux fichiers facultatifs que le générateur de proforma utilise s'ils sont présents.

## `Verdana.ttf` et `Verdana-Bold.ttf`

La charte des documents officiels d'Évents & Studios est en Verdana. La police
n'étant pas libre de redistribution, elle n'est pas embarquée dans le skill :
dépose-la ici et le PDF la reprendra automatiquement. Les noms `verdana.ttf` et
`verdanab.ttf` (ceux de macOS et de Windows) sont aussi reconnus.

Sur macOS, les deux fichiers sont dans `/Library/Fonts/` ou
`~/Library/Fonts/` — un simple `cp` suffit.

Sans eux, le PDF sort en Helvetica, la substitution la plus proche en métrique.

## `logo.png`

Le logo de la société, placé centré en tête du PDF, au-dessus de la raison
sociale, sur 16 mm de haut. PNG ou JPG, de préférence à fond transparent et
d'au moins 400 px de large. Sans lui, le document commence directement par la
raison sociale.
