# Furia Bot MVP

## Configuração do Ambiente

Para executar este projeto, você precisa configurar as seguintes variáveis de ambiente em um arquivo `.env`:

### Variáveis Obrigatórias

```env
# Configurações do MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=furia_bot
```

## Instalação

1. Clone o repositório
2. Crie um arquivo `.env` na raiz do projeto usando as variáveis acima como exemplo
3. Instale as dependências (instruções de instalação serão adicionadas em breve)
4. Execute o bot (instruções de execução serão adicionadas em breve)

## Estrutura do Projeto

- `src/bot/` - Código fonte principal do bot
  - `config/` - Arquivos de configuração
    - `mongodb.py` - Configuração da conexão com MongoDB 