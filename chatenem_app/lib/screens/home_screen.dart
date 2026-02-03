import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../services/chat_api.dart';
import '../screens/chat_drawer.dart';


class HomeScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final ThemeMode themeMode;
  final String? chatId;

  const HomeScreen({
    super.key,
    required this.onToggleTheme,
    required this.themeMode,
    this.chatId,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _controller = TextEditingController();
  final List<Map<String, String>> _messages = [];

  bool _loading = false;
  int guestQuestions = 0;
  final int guestLimit = 3;

  String? chatId;

  @override
  void initState() {
    super.initState();

    if (widget.chatId != null) {
      chatId = widget.chatId;
      _loadMessages();
    } else {
      _loadOrCreateChat();
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    final isGuest = user == null;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      drawer: isGuest
          ? null
          : ChatDrawer(
              chatId: chatId,
              onToggleTheme: widget.onToggleTheme,
              themeMode: widget.themeMode,
            ),


      appBar: AppBar(
        elevation: 0,
        backgroundColor: isDark ? Colors.grey[900] : Colors.white,
        foregroundColor: isDark ? Colors.white : Colors.black,
        title: Text(
          isGuest ? 'ChatENEM (Convidado)' : 'ChatENEM',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        leading: !isGuest
            ? Builder(
                builder: (context) => IconButton(
                  icon: const Icon(Icons.menu),
                  onPressed: () => Scaffold.of(context).openDrawer(),
                ),
              )
            : null,
        actions: [
          // 🌙☀️ BOTÃO DE TEMA
          IconButton(
            icon: Icon(
              widget.themeMode == ThemeMode.dark
                  ? Icons.light_mode
                  : Icons.dark_mode,
            ),
            tooltip: 'Alternar tema',
            onPressed: widget.onToggleTheme,
          ),

          if (!isGuest)
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () async {
                await Supabase.instance.client.auth.signOut();
                if (mounted) {
                  Navigator.pushReplacementNamed(context, '/');
                }
              },
            ),
        ],
      ),

      body: Column(
        children: [
          Expanded(child: _buildMessages()),
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: LinearProgressIndicator(minHeight: 2),
            ),
          _buildInput(isGuest),
        ],
      ),
    );
  }

Widget _buildMessages() {
  return ListView.builder(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
    itemCount: _messages.length,
    itemBuilder: (context, index) {
      final msg = _messages[index];
      final isUser = msg['role'] == 'user';

      return Align(
        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.75,
          ),
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
          decoration: BoxDecoration(
          color: isUser
              ? (Theme.of(context).brightness == Brightness.dark
                  ? Colors.blue.shade700
                  : Colors.blue)
              : (Theme.of(context).brightness == Brightness.dark
                  ? Colors.grey.shade800
                  : Colors.grey.shade200),

            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: Radius.circular(isUser ? 16 : 0),
              bottomRight: Radius.circular(isUser ? 0 : 16),
            ),
          ),
          child: Text(
            msg['text']!,
            style: TextStyle(
            color: isUser
                ? Colors.white
                : (Theme.of(context).brightness == Brightness.dark
                    ? Colors.white
                    : Colors.black87),

              fontSize: 15,
            ),
          ),
        ),
      );
    },
  );
}

Widget _buildInput(bool isGuest) {
  final isDark = Theme.of(context).brightness == Brightness.dark;

  return SafeArea(
    child: Padding(
      padding: const EdgeInsets.all(10),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controller,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendQuestion(isGuest),
              decoration: InputDecoration(
                hintText: 'Digite sua pergunta...',
                filled: true,
                
                fillColor: isDark ? Colors.grey.shade800 : Colors.grey.shade100,

                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(30),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            radius: 24,
            backgroundColor: Colors.blue,
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.white),
              onPressed: _loading ? null : () => _sendQuestion(isGuest),
            ),
          ),
        ],
      ),
    ),
  );
}

  // 🔹 Busca ou cria chat se estiver logado
  Future<void> _loadOrCreateChat() async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;

    final chat = await Supabase.instance.client
        .from('chats')
        .select()
        .eq('user_id', user.id)
        .order('created_at', ascending: false)
        .limit(1)
        .maybeSingle();

    if (chat != null) {
      chatId = chat['id'];
      await _loadMessages();
      return;
    }

    final newChat = await Supabase.instance.client
        .from('chats')
        .insert({
          'user_id': user.id,
          'title': 'Chat ENEM',
        })
        .select()
        .single();

    chatId = newChat['id'];
  }

  // 🔹 Carrega mensagens do chat
  Future<void> _loadMessages() async {
    if (chatId == null) return;

    final response = await Supabase.instance.client
        .from('messages')
        .select()
        .eq('chat_id', chatId!)
        .order('created_at');

    setState(() {
      _messages.clear();
      for (final msg in response) {
        _messages.add({
          'role': msg['sender'] == 'ai' ? 'assistant' : 'user',
          'text': msg['content'],
        });
      }
    });
  }

  // 🔹 Envia pergunta
  Future<void> _sendQuestion(bool isGuest) async {
    final isFirstMessage = _messages.isEmpty;
    final question = _controller.text.trim();
    if (question.isEmpty) return;

    if (isGuest && guestQuestions >= guestLimit) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Faça login para continuar usando o chat'),
        ),
      );
      return;
    }

    setState(() {
      _messages.add({'role': 'user', 'text': question});
      _controller.clear();
      _loading = true;
    });

    try {
      final answer = await ChatApi.ask(question);

      setState(() {
        _messages.add({'role': 'assistant', 'text': answer});
        _loading = false;
        if (isGuest) guestQuestions++;
      });

      final user = Supabase.instance.client.auth.currentUser;
      if (user != null && chatId != null) {

      // 💾 salva mensagens
      await Supabase.instance.client.from('messages').insert([
        {
          'chat_id': chatId,
          'sender': 'user',
          'content': question,
        },
        {
          'chat_id': chatId,
          'sender': 'ai',
          'content': answer,
        }
      ]);

      // 🧠 gerar título automático APENAS na 1ª mensagem
      if (isFirstMessage) {
        final title = await ChatApi.generateTitle(question);

        await Supabase.instance.client
            .from('chats')
            .update({'title': title})
            .eq('id', chatId!);
      }
      }
    } catch (e) {
      setState(() {
        _loading = false;
        _messages.add({
          'role': 'assistant',
          'text': 'Erro ao consultar o servidor.',
        });
      });
    }
  }
}
