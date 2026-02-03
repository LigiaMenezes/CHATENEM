import os
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(["POST"])
def ask(request):
    """
    Endpoint /collector/ask/ aceita JSON { "question": "...", "k": 5(optional), first_question(bool) }.
    Retorna JSON com { answer, citations, found_context, title }.
    """
    # Verificar API Key
    api_key = request.headers.get('Authorization')
    expected_key = f"Bearer {os.environ.get('API_KEY', 'default-secret-key')}"
    print("AUTH RECEBIDO:", api_key)
    print("AUTH ESPERADO:", expected_key)
    # print("HEADERS COMPLETOS:", dict(request.headers))

    if api_key != expected_key:
        return Response({"error": "Unauthorized - Invalid API Key"}, status=status.HTTP_401_UNAUTHORIZED)
    
    question = request.data.get("question") or request.data.get("q")
    if not question:
        return Response({"detail": "campo 'question' obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        k = int(request.data.get("k", 5))
        if k <= 0 or k >= 100:
            return Response({"detail": "Parameter 'k' must be positive and less than 100"}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        k = 5
    
    try:
        from .agent import answer_question
        from .title_generator import title_generator
        result = answer_question(question, k=k)
        first_question = request.data.get("first_question")
        if first_question:
            result["title"] = title_generator(question)
        return Response(
                result,
                content_type="application/json; charset=utf-8"
            )

    except Exception as e:
        return Response({
            "answer": "Erro interno. Pergunta: " + question,
            "citations": [],
            "found_context": False,
            "error": str(e)
        })

