# Relatório — estrutura

Esqueleto das seções pedidas para o checkpoint. Cada seção indica a fonte do conteúdo.

1. **Introdução histórica**: Dijkstra (1965), reformulação de Hoare
2. **Conceitos**: seção crítica, exclusão mútua, condição de corrida, deadlock, starvation, livelock
3. **Condições de Coffman (1971)**: as quatro condições e como cada solução quebra uma delas
4. **Soluções implementadas**: descrição + pseudocódigo de cada arquivo em `src/jantar/estrategias/`
5. **Implementação**: threads, locks, detector de deadlock (grafo de espera), forçar deadlock
6. **Resultados da simulação**: tabela gerada por `python -m jantar.benchmark` (normal e com
   `--forcar-deadlock`) + gráfico de refeições por filósofo e espera máxima por estratégia
7. **Aplicações práticas**: PIX/transferências, bancos de dados, trânsito, kernel
8. **Outros problemas clássicos**: produtor–consumidor, leitores–escritores, barbeiro dorminhoco
9. **Conclusão**
10. **Referências**: Tanenbaum (Sistemas Operacionais Modernos), Silberschatz (Fundamentos de SO),
    Dijkstra (1965), Coffman et al. (1971), Chandy & Misra (1984)
