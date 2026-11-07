# US-01: Cadastro de Novos Livros no Acervo via Agente Conversacional

## 1. Identificação e Metadados
* **ID:** US-01
* **Título:** Cadastro de Novos Livros no Acervo
* **Épico:** Gestão do Acervo da Biblioteca
* **Persona:** Bibliotecário(a) / Gestor(a) do Acervo
* **Prioridade:** Alta (Must Have)
* **Estimativa:** 5 Story Points

---

## 2. Narrativa da História (Padrão Connextra)
> **Como** bibliotecário(a) / gestor(a) do acervo,  
> **Quero** conversar com um agente inteligente para registrar novos livros no catálogo da biblioteca,  
> **Para que** o acervo permaneça devidamente catalogado, atualizado e pronto para consulta e empréstimo aos leitores.

---

## 3. Regras de Negócio e Modelo de Dados

### 3.1. Atributos da Entidade Livro
| Campo | Tipo | Obrigatório? | Descrição / Validação |
| :--- | :--- | :---: | :--- |
| **id** | Inteiro | Sim (Automático) | Identificador único no sistema |
| **titulo** | Texto | Sim | Nome da obra (não pode ser em branco) |
| **autor** | Texto | Sim | Nome do(s) autor(es) (não pode ser em branco) |
| **isbn** | Texto | Sim | Código ISBN com 10 ou 13 dígitos numéricos válidos |
| **ano_publicacao** | Inteiro | Sim | Ano de publicação válido (entre 1 e ano atual) |
| **genero** | Texto | Sim | Categoria literária ou área temática |
| **quantidade_exemplares** | Inteiro | Sim | Número de cópias disponíveis ($\ge 1$) |
| **criado_em** | Data/Hora | Sim (Automático) | Data e hora de inclusão do registro |

### 3.2. Regras de Comportamento do Agente
1. **Diálogo Flexível:** O bibliotecário pode informar todos os dados em uma única sentença (ex.: *"Cadastre o livro 1984 de George Orwell, ISBN 9780451524935, ano 1949, ficção, 3 exemplares"*) ou de forma guiada passo a passo.
2. **Preenchimento de Lacunas (Slot-filling):** O agente deve detectar quais informações ainda faltam e solicitá-las uma a uma.
3. **Resumo e Confirmação Prévia:** Antes de persistir qualquer livro no banco de dados, o agente deve exibir o resumo formatado dos dados coletados e aguardar a confirmação explícita (`sim`/`não`).
4. **Tratamento de Duplicidade:** Caso o ISBN informado já pertença a um livro cadastrado, o agente deve informar o usuário e oferecer a opção de apenas somar novos exemplares ao registro pré-existente.
5. **Cancelamento a Qualquer Momento:** O usuário pode dizer `cancelar` a qualquer momento para abortar o fluxo de cadastro sem alterar a base.

---

## 4. Critérios de Aceite (BDD / Gherkin)

### Cenário 1: Cadastro completo com sucesso (Fluxo Principal)
```gherkin
Funcionalidade: Cadastro de Livros no Acervo
  Cenário: Cadastro bem-sucedido via agente conversacional
    Dado que o bibliotecário inicia o cadastro de um livro
    Quando fornecer todas as informações válidas (Título, Autor, ISBN, Ano, Gênero e Quantidade)
    E o agente apresentar o resumo dos dados para confirmação
    E o bibliotecário responder "sim"
    Então o livro deve ser persistido no banco de dados
    E o agente deve retornar mensagem de sucesso contendo o ID e os detalhes do livro cadastrado.
```

### Cenário 2: Coleta incremental de informações pendentes
```gherkin
  Cenário: Solicitação guiada de dados faltantes
    Dado que o bibliotecário informa apenas o título da obra (ex: "Quero cadastrar Dom Casmurro")
    Quando o agente processar a mensagem
    Então o agente deve registrar o título coletado
    E solicitar o próximo dado pendente (Autor) de maneira amigável
    E continuar a coleta sequencial até que todos os campos obrigatórios estejam preenchidos.
```

### Cenário 3: Validação de entradas inválidas
```gherkin
  Cenário: Validação de ISBN e campos numéricos
    Dado que o bibliotecário fornece um ISBN inválido ("123-abc") ou quantidade zero
    Quando o agente validar a informação
    Então o agente deve rejeitar o valor inválido
    E exibir uma mensagem clara explicando o motivo do erro e o formato esperado
    E solicitar novamente apenas o campo inconsistente, mantendo os dados anteriores já coletados.
```

### Cenário 4: Identificação de ISBN duplicado (Incremento de Exemplares)
```gherkin
  Cenário: Tentativa de cadastro de ISBN já existente
    Dado que o livro com ISBN "9788535902778" já existe no catálogo com 2 exemplares
    Quando o bibliotecário tentar cadastrar um novo livro com o mesmo ISBN informando 3 exemplares
    Então o agente deve alertar que o livro já se encontra no acervo
    E perguntar se deseja acrescentar os 3 exemplares ao estoque (totalizando 5)
    E, após confirmação, atualizar o número de exemplares no acervo sem criar duplicata.
```

### Cenário 5: Cancelamento da operação
```gherkin
  Cenário: Abortar cadastro em andamento
    Dado que o bibliotecário está em qualquer etapa do fluxo de cadastro
    Quando digitar "cancelar" ou "abortar"
    Então o agente deve limpar o estado temporário
    E confirmar que o cadastro foi cancelado sem salvar nada no banco de dados.
```
