import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

class AuthGate extends StatelessWidget {
  final VoidCallback onToggleTheme;
  final ThemeMode themeMode;

  const AuthGate({
    super.key,
    required this.onToggleTheme,
    required this.themeMode,
  });

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<AuthState>(
      stream: Supabase.instance.client.auth.onAuthStateChange,
      builder: (context, snapshot) {
        final session = Supabase.instance.client.auth.currentSession;

        if (session != null) {
          return HomeScreen(
            onToggleTheme: onToggleTheme,
            themeMode: themeMode,
          );
        }


        return LoginScreen(
          onToggleTheme: onToggleTheme,
          themeMode: themeMode,
        );
      },
    );
  }
}
