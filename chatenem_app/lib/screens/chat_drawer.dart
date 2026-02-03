import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../screens/home_screen.dart';

class ChatDrawer extends StatefulWidget {
  final String? chatId;
  final VoidCallback onToggleTheme;
  final ThemeMode themeMode;

  const ChatDrawer({
    super.key,
    this.chatId,
    required this.onToggleTheme,
    required this.themeMode,
  });

  @override
  State<ChatDrawer> createState() => _ChatDrawerState();
}


class _ChatDrawerState extends State<ChatDrawer> {
  List chats = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _loadChats();
  }

  Future<void> _loadChats() async {
    final user = Supabase.instance.client.auth.currentUser;
    if (user == null) return;

    final data = await Supabase.instance.client
        .from('chats')
        .select()
        .eq('user_id', user.id)
        .order('created_at', ascending: false);

    setState(() {
      chats = data;
      loading = false;
    });
  }

  // ✏️ Renomear
  Future<void> _renameChat(String chatId, String currentTitle) async {
    final controller = TextEditingController(text: currentTitle);

    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Renomear chat'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Novo título',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              await Supabase.instance.client
                  .from('chats')
                  .update({'title': controller.text.trim()})
                  .eq('id', chatId);

              Navigator.pop(context);
              _loadChats();
            },
            child: const Text('Salvar'),
          ),
        ],
      ),
    );
  }

  // 🗑️ Apagar
  Future<void> _deleteChat(String chatId) async {
    await Supabase.instance.client
        .from('messages')
        .delete()
        .eq('chat_id', chatId);

    await Supabase.instance.client
        .from('chats')
        .delete()
        .eq('id', chatId);

    _loadChats();
  }

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    final avatarUrl =
        user?.userMetadata?['avatar_url'] ??
        user?.userMetadata?['picture'];
    final fullName = user?.userMetadata?['full_name'] ?? 'Usuário';
    final scheme = Theme.of(context).colorScheme;
    return Drawer(
      child: Column(
        children: [

          // 👤 HEADER
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(16, 40, 16, 20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Theme.of(context).primaryColor,
                  Theme.of(context).primaryColor.withOpacity(0.85),
                ],
              ),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: Colors.white,
                  backgroundImage:
                      avatarUrl != null ? NetworkImage(avatarUrl) : null,
                  child: avatarUrl == null
                      ? Text(
                          fullName[0],
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        )
                      : null,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        fullName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        user?.email ?? '',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // 📜 CHATS
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.separated(
                    padding: const EdgeInsets.all(8),
                    itemCount: chats.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 4),
                    itemBuilder: (context, index) {
                      final chat = chats[index];
                      final theme = Theme.of(context);
                      final isDark = theme.brightness == Brightness.dark;

                      return Material(
                        borderRadius: BorderRadius.circular(12),
                        color: theme.colorScheme.surface,
                        elevation: isDark ? 0 : 2,
                        child: ListTile(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          title: Text(
                            chat['title'] ?? 'Chat sem título',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                             style: TextStyle(
                              color: theme.colorScheme.onSurface,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          leading: const Icon(Icons.chat_bubble_outline),
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'edit') {
                                _renameChat(
                                  chat['id'],
                                  chat['title'] ?? '',
                                );
                              } else if (value == 'delete') {
                                _deleteChat(chat['id']);
                              }
                            },
                            itemBuilder: (_) => const [
                              PopupMenuItem(
                                value: 'edit',
                                child: Text('Renomear'),
                              ),
                              PopupMenuItem(
                                value: 'delete',
                                child: Text('Apagar'),
                              ),
                            ],
                          ),
                          onTap: () {
                            Navigator.pop(context);
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    HomeScreen(
                                      chatId: chat['id'],
                                      onToggleTheme: widget.onToggleTheme,
                                      themeMode: widget.themeMode,

                                    )

                              ),
                            );
                          },
                        ),
                      );
                    },
                  ),
          ),

          // 🚪 SAIR
          
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(8),
              
              child: ListTile(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                 tileColor: scheme.errorContainer,
                  leading: Icon(
                    Icons.logout,
                    color: scheme.onErrorContainer,
                  ),
                  title: Text(
                    'Sair',
                    style: TextStyle(
                      color: scheme.onErrorContainer,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                onTap: () async {
                  await Supabase.instance.client.auth.signOut();
                  if (mounted) {
                    Navigator.pushReplacementNamed(context, '/');
                  }
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
