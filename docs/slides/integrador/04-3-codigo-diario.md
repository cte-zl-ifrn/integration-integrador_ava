# Identificando um código de diário

No SUAP um curso é formado por vários componentes currículares que são ofertados em períodos na forma de turmas, isto gera um código único de diário.

O código do diário é formado pela concateção do código da turma e pelo código do componente currícular, separados por ".", mais o ID do diário. No exemplo abaixo o código do diário seria "`20212.1.011001.1P`.**FIC007**#<u>123456</u>", onde:

* `20212.1.011001.1P` - *código da turma*, onde:
  * `20212` - *ano/período de oferta do componente*, no caso, ofertado em 2021, período 2.
  * `1` - *período da turma*, no caso, esta e é o primeiro perído do turma, ou seja, a turma se iniciou no 2º período de 2021 mesmo.
  * `011001` - *código do curso*, no caso, é o código do curso de "Operador de sistemas".
  * `1P` - *identificação da turma*, no caso, é arbitrado pela área acadêmica do campus/instituição.
* **FIC007** - *código do componente currícular*, no caso, FIC007 indicaria o componente "Planilhas eletrônicas - Fundamental".
* <u>123456</u> - *ID do diário no SUAP*, no caso, #123456 indicaria o diário cujo ID é "123456". *Antes não tinha este elemento, foi adicionado pois um diário pode ser dividido e isso causaria inconsistência.
