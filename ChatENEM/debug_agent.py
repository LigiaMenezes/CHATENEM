import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IFPIChat.settings')
django.setup()

from collector.agent import answer_question

# Configurar encoding para UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def test_agent():
    """Testa o agente de resposta"""
    print("=== Teste do Agente ===")
    
    # Perguntas de teste
    questions = [
        "Quais são os cursos oferecidos pelo IFPI?",
        "Quais são os atalhos de acessibilidade do site do IFPI?",
        "Como entrar em contato com o IFPI?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Pergunta: {question}")
        print("-" * 50)
        
        try:
            result = answer_question(question, k=5)
            
            print(f"Resposta: {result['answer']}")
            print(f"Contexto encontrado: {result['found_context']}")
            print(f"Citações: {len(result['citations'])}")
            
            if result['citations']:
                print("\nCitações:")
                for j, citation in enumerate(result['citations'], 1):
                    print(f"  {j}. Score: {citation['score']:.3f}")
                    print(f"     Título: {citation.get('document_title', 'N/A')}")
                    print(f"     Trecho: {citation['excerpt'][:100]}...")
            
        except Exception as e:
            print(f"ERRO: {e}")
        
        print("=" * 60)

if __name__ == "__main__":
    test_agent()