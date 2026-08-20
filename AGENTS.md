# Instruções obrigatórias para agentes

Estas regras valem para qualquer agente, modelo ou colaborador que altere este projeto.

## Fluxo GitHub

1. Antes de iniciar qualquer correção, melhoria, refatoração ou funcionalidade, crie uma issue no GitHub com objetivo, escopo e critérios de aceite.
2. Crie uma branch dedicada a partir da branch de destino. Não faça mudanças diretamente na branch protegida.
3. Entregue toda alteração por pull request. O PR deve ter escopo pequeno, testes proporcionais ao risco e evidências das verificações executadas.
4. A descrição do PR deve mencionar a issue usando `Closes #<número>` quando o merge resolver a tarefa ou `Refs #<número>` quando houver apenas relação.
5. Deploys devem partir de commits revisados e aprovados por PR. Não faça deploy de mudanças locais ou commits sem revisão.
6. Se uma nova tarefa for descoberta durante a implementação e estiver fora do escopo, registre outra issue antes de executá-la.

## Qualidade mínima

- Preserve compatibilidade, acessibilidade e privacidade dos dados.
- Rode lint, contratos arquiteturais e testes unitários, de integração e E2E aplicáveis.
- Não versione segredos. Integrações externas devem ser configuradas por variáveis de ambiente.
- Interfaces assíncronas devem oferecer skeleton, carregamento progressivo ou lazy loading, progresso compreensível e estados de sucesso/erro.
- Motion deve ser funcional, sutil, interrompível e respeitar `prefers-reduced-motion`.

