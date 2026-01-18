```mermaid
---
config:
  flowchart:
    curve: stepBefore
  theme: base
  themeVariables:
    fontFamily: 'monospace'
    primaryColor: '#0e0e0eff' # Used for primary items like nodes and edges
    primaryTextColor: '#ffffffff' # Used for text on primary items
    primaryBorderColor: '#ffffffff' # Used for borders around primary items
    lineColor: '#ffffffff' # Used for lines and edges
    secondaryColor: '#ffffffff' # Used for secondary items like sub-nodes
    secondaryTextColor: '#000000ff' # Used for text on secondary items
    secondaryBorderColor: '#000000ff' # Used for borders around secondary items
    tertiaryColor: '#000000ff' # Used for tertiary items like sub-nodes
    tertiaryTextColor: '#ffffffff' # Used for text on tertiary items
    tertiaryBorderColor: '#ffffffff' # Used for borders around tertiary items
    tertiaryBackgroundColor: '#ffffffff' # Used for background of tertiary items
    tertiaryLabelColor: '#ffffffff' # Used for labels on tertiary items
---

flowchart LR

AA  --- BA
AA  --- BB
BB  --- CA
CA  --- BA
DA  --- CA


AA[SPACE<br>Σ]
BA[PRICE]
BB[SIZE]
CA[FREIGHT]
DA[WEIGHT]
