# Identificando um código de diário

No SUAP um curso é formado por vários componentes currículares que são ofertados em períodos na forma de turmas, isto
gera um **código de diário**, o qual é formado pela concateção do **código da turma** e pelo
**código do componente currícular**, separados por ".", mais o **ID do diário**. No exemplo onde o código do diário
seja "`20212.1.011001.1P`.**FIC007**#_123456_":

* `20212.1.011001.1P` - _código da turma_, onde:
  * `20212` - _ano/período de oferta do componente_, no caso, ofertado em 2021, período 2.
  * `1` - _período da turma_, no caso, esta e é o primeiro perído do turma, ou seja, a turma se iniciou no 2º período
     de 2021 mesmo.
  * `011001` - _código do curso_, no caso, é o código do curso de "Operador de sistemas".
  * `1P` - _identificação da turma_, no caso, é arbitrado pela área acadêmica do campus/instituição.
* **FIC007** - _código do componente currícular_, no caso, FIC007 indicaria o componente "Planilhas eletrônicas -
  Fundamental".
* _123456_ - _ID do diário no SUAP_, no caso, #123456 indicaria o diário cujo ID é "123456". *Antes não tinha
  este elemento, foi adicionado pois um diário pode ser dividido e isso causaria inconsistência.
