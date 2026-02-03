import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ChatApi {
  // 🧠 Gera título curto para o chat
static Future<String> generateTitle(String question) async {
  final response = await ask(
    'Crie um título curto (máx 6 palavras) para a pergunta abaixo. '
    'Retorne SOMENTE o título, sem aspas.\n\nPergunta: $question',
  );

  return response
      .replaceAll('"', '')
      .replaceAll('\n', '')
      .trim();
}


  static Future<String> ask(String question, {String? subject}) async {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/ask/');

    final body = {
      'question': question,
      'first_question': false,
      if (subject != null && subject != 'Todos') 'subject': subject,
    };

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode != 200) {
      throw Exception('Erro ao consultar o servidor: ${response.statusCode}');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return data['answer'];
  }

  static Stream<String> askStream(String question, {String? subject}) async* {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/ask-stream/');

    final body = {
      'question': question,
      'first_question': false,
      if (subject != null && subject != 'Todos') 'subject': subject,
    };

    final request = http.Request('POST', uri)
      ..headers.addAll({
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
      })
      ..body = jsonEncode(body);

    final streamedResponse = await request.send();

    if (streamedResponse.statusCode != 200) {
      throw Exception('Erro ao consultar o servidor: ${streamedResponse.statusCode}');
    }

    await for (final chunk in streamedResponse.stream.transform(utf8.decoder)) {
      // Processa cada chunk do stream
      final lines = chunk.split('\n');
      for (final line in lines) {
        if (line.startsWith('data: ')) {
          final data = line.substring(6);
          if (data == '[DONE]') break;
          
          try {
            final jsonData = jsonDecode(data);
            if (jsonData['choices'] != null && 
                jsonData['choices'][0]['delta']['content'] != null) {
              yield jsonData['choices'][0]['delta']['content'];
            }
          } catch (e) {
            // Ignora erros de parsing, continua com o stream
            continue;
          }
        }
      }
    }
  }

  // Método alternativo para simulação de streaming se o backend não suportar
  static Stream<String> askStreamSimulated(String question, {String? subject}) async* {
    // Primeiro, obtém a resposta completa
    final fullAnswer = await ask(question, subject: subject);
    
    // Simula streaming dividindo em palavras
    final words = fullAnswer.split(' ');
    
    for (final word in words) {
      yield '$word ';
      await Future.delayed(const Duration(milliseconds: 50));
    }
  }

  // Método para buscar histórico de chats do usuário
  static Future<List<Map<String, dynamic>>> getUserChats(String userId) async {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/chats/');

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
        'X-User-ID': userId,
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Erro ao buscar chats: ${response.statusCode}');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return List<Map<String, dynamic>>.from(data['chats'] ?? []);
  }

  // Método para buscar histórico de mensagens de um chat
  static Future<List<Map<String, dynamic>>> getChatMessages(String chatId) async {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/chats/$chatId/messages/');

    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
      },
    );

    if (response.statusCode != 200) {
      throw Exception('Erro ao buscar mensagens: ${response.statusCode}');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return List<Map<String, dynamic>>.from(data['messages'] ?? []);
  }

  // Método para criar um novo chat
  static Future<Map<String, dynamic>> createChat({
    required String userId,
    String? subject,
    String? title,
  }) async {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/chats/');

    final body = {
      'user_id': userId,
      'title': title ?? (subject != null ? 'Chat ENEM - $subject' : 'Chat ENEM'),
      if (subject != null && subject != 'Todos') 'subject': subject,
    };

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode != 201) {
      throw Exception('Erro ao criar chat: ${response.statusCode}');
    }

    final data = jsonDecode(utf8.decode(response.bodyBytes));
    return data;
  }

  // Método para salvar mensagens no histórico
  static Future<void> saveMessage({
    required String chatId,
    required String sender,
    required String content,
  }) async {
    final uri = Uri.parse('${dotenv.env['DJANGO_URL']}/collector/messages/');

    final body = {
      'chat_id': chatId,
      'sender': sender,
      'content': content,
    };

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ${dotenv.env['API_KEY']}',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode != 201) {
      throw Exception('Erro ao salvar mensagem: ${response.statusCode}');
    }
  }
}