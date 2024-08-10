# Gestão Otimizada da Alocação de Recursos às Ordens de Serviço

Este repositório contém o código desenvolvido como parte do Trabalho de Conclusão de Curso, apresentado ao curso de Engenharia de Sistemas da Universidade Federal de Minas Gerais. O projeto aborda a otimização da alocação de recursos em empresas que operam com múltiplos depósitos, com o objetivo de maximizar a eficiência operacional e a economia de recursos.

## Resumo do Projeto

O projeto consiste no desenvolvimento de um modelo matemático para a alocação eficiente de recursos em uma empresa com múltiplos depósitos. O objetivo principal é priorizar a execução de obras considerando os materiais disponíveis em cada depósito, buscando maximizar a soma das prioridades das obras realizadas. Além disso, o projeto explora a viabilidade do transporte de materiais entre os depósitos, considerando os custos envolvidos.

## Estrutura dos Arquivos

- `solucao_empresa.py`: Implementação da leitura das informações da solução adotada pela empresa sem a utilização dos modelos de otimização.
-  `otimizacao_individual.py`: Código que realiza a otimização individual dos depósitos, sem considerar o transporte de materiais entre eles.
- `otimizacao_com_transporte.py`: Código que implementa o modelo de otimização envolvendo todos os depósitos simultaneamente, considerando a possibilidade de materiais entre os depósitos.
