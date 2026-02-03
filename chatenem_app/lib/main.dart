import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'auth_gate.dart';
import 'screens/theme_controller.dart';


Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: 'assets/.env');

  await Supabase.initialize(
    url: dotenv.env['SUPABASE_URL']!,
    anonKey: dotenv.env['SUPABASE_KEY']!,
  );

  runApp(const ChatENEMApp());
}
class ChatENEMApp extends StatefulWidget {
  const ChatENEMApp({super.key});

  @override
  State<ChatENEMApp> createState() => _ChatENEMAppState();
}

class _ChatENEMAppState extends State<ChatENEMApp> {
  ThemeMode _themeMode = ThemeMode.light;

  void toggleTheme() {
    setState(() {
      _themeMode =
          _themeMode == ThemeMode.light ? ThemeMode.dark : ThemeMode.light;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,

      themeMode: _themeMode,

      theme: ThemeData(
        brightness: Brightness.light,
        useMaterial3: true,
      ),

      darkTheme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
      ),

      home: AuthGate(
        onToggleTheme: toggleTheme,
        themeMode: _themeMode,
      ),
    );
  }
}
